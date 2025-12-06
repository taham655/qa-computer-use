"""
Test Executor - Uses computer-use tools to execute generated test cases.
Integrates with Claude to interpret test steps and interact with the browser.
"""

import asyncio
import base64
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Callable

from anthropic import Anthropic
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaMessageParam,
    BetaTextBlockParam,
)

from computer_use_demo.tools import ToolCollection, ToolResult, TOOL_GROUPS_BY_VERSION
from .test_generator import TestCase, TestStep


class TestStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class StepResult:
    """Result of executing a single test step."""
    step: TestStep
    status: TestStatus
    actual_result: str | None = None
    error_message: str | None = None
    screenshot_base64: str | None = None
    duration_ms: int = 0


@dataclass
class TestResult:
    """Result of executing a complete test case."""
    test_case: TestCase
    status: TestStatus
    step_results: list[StepResult] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    error_message: str | None = None

    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_case.id,
            "test_name": self.test_case.name,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "step_results": [
                {
                    "step_order": sr.step.order,
                    "action": sr.step.action,
                    "target": sr.step.target,
                    "status": sr.status,
                    "actual_result": sr.actual_result,
                    "error": sr.error_message,
                    "duration_ms": sr.duration_ms,
                }
                for sr in self.step_results
            ],
            "error": self.error_message,
        }


@dataclass
class TestSuiteResult:
    """Result of executing a test suite."""
    results: list[TestResult] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def total_tests(self) -> int:
        return len(self.results)

    @property
    def passed_tests(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.PASSED)

    @property
    def failed_tests(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.FAILED)

    @property
    def error_tests(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.ERROR)

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests * 100

    def to_dict(self) -> dict:
        return {
            "total_tests": self.total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "errors": self.error_tests,
            "pass_rate": f"{self.pass_rate:.1f}%",
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0,
            "results": [r.to_dict() for r in self.results],
        }


class TestExecutor:
    """
    Executes test cases using Claude with computer-use tools.

    The executor:
    1. Takes generated test cases
    2. Uses Claude to interpret each step
    3. Uses computer tools to interact with the browser
    4. Captures screenshots and results
    5. Reports pass/fail status
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        tool_version: str = "computer_use_20250124",
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.tool_version = tool_version
        self.client = Anthropic(api_key=self.api_key)

        # Initialize tools
        tool_group = TOOL_GROUPS_BY_VERSION[tool_version]
        self.tool_collection = ToolCollection(*(ToolCls() for ToolCls in tool_group.tools))

    async def execute_test_suite(
        self,
        test_cases: list[TestCase],
        base_url: str,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> TestSuiteResult:
        """
        Execute a full test suite.

        Args:
            test_cases: List of test cases to execute
            base_url: Base URL of the application being tested
            progress_callback: Optional callback(test_name, current, total)
        """
        suite_result = TestSuiteResult(start_time=datetime.now())

        for i, test_case in enumerate(test_cases):
            if progress_callback:
                progress_callback(test_case.name, i + 1, len(test_cases))

            result = await self.execute_test(test_case, base_url)
            suite_result.results.append(result)

        suite_result.end_time = datetime.now()
        return suite_result

    async def execute_test(
        self,
        test_case: TestCase,
        base_url: str,
    ) -> TestResult:
        """
        Execute a single test case using Claude with computer-use.
        """
        result = TestResult(
            test_case=test_case,
            status=TestStatus.RUNNING,
            start_time=datetime.now(),
        )

        try:
            # Build the prompt for Claude
            prompt = self._build_test_prompt(test_case, base_url)

            # Execute with Claude
            messages: list[BetaMessageParam] = [
                {"role": "user", "content": prompt}
            ]

            # Run the agentic loop
            all_passed = True
            step_index = 0

            while True:
                response = self.client.beta.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=messages,
                    tools=self.tool_collection.to_params(),
                    betas=[TOOL_GROUPS_BY_VERSION[self.tool_version].beta_flag] if TOOL_GROUPS_BY_VERSION[self.tool_version].beta_flag else [],
                )

                # Process response
                assistant_content = []
                tool_results = []

                for block in response.content:
                    if hasattr(block, "text"):
                        assistant_content.append({"type": "text", "text": block.text})

                        # Check for step completion markers in Claude's response
                        if "STEP_PASSED" in block.text:
                            if step_index < len(test_case.steps):
                                step_result = StepResult(
                                    step=test_case.steps[step_index],
                                    status=TestStatus.PASSED,
                                    actual_result="Step completed successfully",
                                )
                                result.step_results.append(step_result)
                                step_index += 1
                        elif "STEP_FAILED" in block.text:
                            if step_index < len(test_case.steps):
                                step_result = StepResult(
                                    step=test_case.steps[step_index],
                                    status=TestStatus.FAILED,
                                    error_message=block.text,
                                )
                                result.step_results.append(step_result)
                                all_passed = False
                                step_index += 1
                        elif "TEST_COMPLETE" in block.text:
                            break

                    elif hasattr(block, "type") and block.type == "tool_use":
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })

                        # Execute the tool
                        tool_result = await self.tool_collection.run(
                            name=block.name,
                            tool_input=block.input,
                        )

                        # Build tool result content
                        content = []
                        if tool_result.output:
                            content.append({"type": "text", "text": tool_result.output})
                        if tool_result.base64_image:
                            content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": tool_result.base64_image,
                                }
                            })
                        if tool_result.error:
                            content.append({"type": "text", "text": f"Error: {tool_result.error}"})

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": content if content else "Tool executed successfully",
                        })

                # Add assistant message
                messages.append({"role": "assistant", "content": assistant_content})

                # If there were tool uses, add the results
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                else:
                    # No tool uses means we're done
                    break

                # Check for stop reason
                if response.stop_reason == "end_turn":
                    break

            # Set final status
            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED

        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)

        result.end_time = datetime.now()
        return result

    def _build_test_prompt(self, test_case: TestCase, base_url: str) -> str:
        """Build the prompt for Claude to execute a test case."""
        steps_text = "\n".join([
            f"{step.order}. {step.action.upper()}: {step.target}"
            + (f" (value: {step.value})" if step.value else "")
            + (f" [Expected: {step.expected_result}]" if step.expected_result else "")
            for step in test_case.steps
        ])

        test_data_text = json.dumps(test_case.test_data, indent=2) if test_case.test_data else "None"

        return f"""You are a QA automation assistant. Execute the following test case by interacting with the browser.

## Test Case: {test_case.name}

**Description:** {test_case.description}
**Priority:** {test_case.priority}
**Type:** {test_case.test_type}

### Preconditions:
{chr(10).join('- ' + p for p in test_case.preconditions) if test_case.preconditions else '- None'}

### Test Data:
```json
{test_data_text}
```

### Steps to Execute:
{steps_text}

## Instructions:

1. Start by navigating to {base_url} if not already there
2. Execute each step in order using the computer tools
3. After each step, verify the expected result if specified
4. Take screenshots at key moments
5. After completing each step, output "STEP_PASSED" or "STEP_FAILED: <reason>"
6. When all steps are complete, output "TEST_COMPLETE"

## Important:
- Use the `computer` tool to interact with the screen
- For clicking, use `left_click` with coordinates or navigate using `type` and `key`
- For forms, use `type` to enter text
- For navigation, use Firefox's address bar
- Wait for pages to load before interacting
- If an element is not visible, try scrolling

Begin executing the test now."""


class TestReporter:
    """Generates test execution reports."""

    @staticmethod
    def generate_html_report(suite_result: TestSuiteResult, output_path: str | None = None) -> str:
        """Generate an HTML report of test results."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Execution Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; background: #1a1a2e; color: #e8e8f0; }}
        .header {{ background: linear-gradient(90deg, #00d4ff, #ff0080); padding: 30px; border-radius: 12px; color: white; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #2a2a4a; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; color: #00d4ff; }}
        .stat-label {{ color: #9090a0; text-transform: uppercase; font-size: 0.8em; }}
        .test-card {{ background: #2a2a4a; padding: 20px; border-radius: 8px; margin-bottom: 15px; }}
        .test-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .status-passed {{ color: #4ade80; }}
        .status-failed {{ color: #f87171; }}
        .status-error {{ color: #fbbf24; }}
        .step {{ padding: 10px; margin: 5px 0; background: #1a1a2e; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Test Execution Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <div class="stat-card">
            <div class="stat-number">{suite_result.total_tests}</div>
            <div class="stat-label">Total Tests</div>
        </div>
        <div class="stat-card">
            <div class="stat-number status-passed">{suite_result.passed_tests}</div>
            <div class="stat-label">Passed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number status-failed">{suite_result.failed_tests}</div>
            <div class="stat-label">Failed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{suite_result.pass_rate:.1f}%</div>
            <div class="stat-label">Pass Rate</div>
        </div>
    </div>

    <h2>Test Results</h2>
"""

        for result in suite_result.results:
            status_class = f"status-{result.status.value}"
            html += f"""
    <div class="test-card">
        <div class="test-header">
            <h3>{result.test_case.name}</h3>
            <span class="{status_class}">{result.status.value.upper()}</span>
        </div>
        <p>{result.test_case.description}</p>
        <p>Duration: {result.duration_seconds:.2f}s</p>
        <h4>Steps:</h4>
"""
            for step_result in result.step_results:
                step_status_class = f"status-{step_result.status.value}"
                html += f"""
        <div class="step">
            <span class="{step_status_class}">●</span>
            Step {step_result.step.order}: {step_result.step.action} - {step_result.step.target}
            {f'<br><small style="color: #f87171;">Error: {step_result.error_message}</small>' if step_result.error_message else ''}
        </div>
"""
            html += "</div>"

        html += """
</body>
</html>
"""

        if output_path:
            with open(output_path, "w") as f:
                f.write(html)

        return html

    @staticmethod
    def generate_json_report(suite_result: TestSuiteResult, output_path: str | None = None) -> str:
        """Generate a JSON report of test results."""
        json_data = json.dumps(suite_result.to_dict(), indent=2)

        if output_path:
            with open(output_path, "w") as f:
                f.write(json_data)

        return json_data
