"""
AI-powered Test Case Generator using OpenAI (default) or Claude.
"""

import json
import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import openai
from anthropic import Anthropic
from pydantic import BaseModel, Field

from .flow_graph import FlowGraph, Node, Edge, EdgeType


class TestPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestType(StrEnum):
    HAPPY_PATH = "happy_path"
    EDGE_CASE = "edge_case"
    ERROR_HANDLING = "error_handling"
    BOUNDARY = "boundary"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"


@dataclass
class TestStep:
    """A single step in a test case."""
    order: int
    action: str  # e.g., "click", "type", "navigate", "assert"
    target: str  # CSS selector, URL, or element description
    value: str | None = None  # Input value if applicable
    expected_result: str | None = None
    screenshot: bool = False

    def to_dict(self) -> dict:
        return {
            "order": self.order,
            "action": self.action,
            "target": self.target,
            "value": self.value,
            "expected_result": self.expected_result,
            "screenshot": self.screenshot,
        }


@dataclass
class TestCase:
    """A complete test case with steps and metadata."""
    id: str
    name: str
    description: str
    test_type: TestType
    priority: TestPriority
    steps: list[TestStep] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    test_data: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    estimated_duration_seconds: int = 30

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.test_type,
            "priority": self.priority,
            "steps": [s.to_dict() for s in self.steps],
            "preconditions": self.preconditions,
            "test_data": self.test_data,
            "tags": self.tags,
            "estimated_duration": self.estimated_duration_seconds,
        }

    def to_playwright(self) -> str:
        """Generate Playwright test code."""
        lines = [
            f"test('{self.name}', async ({{ page }}) => {{",
            f"  // {self.description}",
        ]

        for step in self.steps:
            if step.action == "navigate":
                lines.append(f"  await page.goto('{step.target}');")
            elif step.action == "click":
                lines.append(f"  await page.click('{step.target}');")
            elif step.action == "type":
                lines.append(f"  await page.fill('{step.target}', '{step.value}');")
            elif step.action == "assert_visible":
                lines.append(f"  await expect(page.locator('{step.target}')).toBeVisible();")
            elif step.action == "assert_text":
                lines.append(f"  await expect(page.locator('{step.target}')).toContainText('{step.value}');")
            elif step.action == "assert_url":
                lines.append(f"  await expect(page).toHaveURL(/{step.target}/);")
            elif step.action == "wait":
                lines.append(f"  await page.waitForTimeout({step.value});")
            elif step.action == "screenshot":
                lines.append(f"  await page.screenshot({{ path: 'screenshots/{self.id}.png' }});")

            if step.expected_result:
                lines.append(f"  // Expected: {step.expected_result}")

        lines.append("});")
        return "\n".join(lines)

    def to_natural_language(self) -> str:
        """Generate human-readable test instructions."""
        lines = [
            f"## Test: {self.name}",
            f"**Priority:** {self.priority}",
            f"**Type:** {self.test_type}",
            "",
            f"**Description:** {self.description}",
            "",
            "### Preconditions:",
        ]

        for pre in self.preconditions:
            lines.append(f"- {pre}")

        lines.extend(["", "### Steps:"])

        for step in self.steps:
            action_desc = f"{step.order}. **{step.action.upper()}**: {step.target}"
            if step.value:
                action_desc += f" with value `{step.value}`"
            lines.append(action_desc)
            if step.expected_result:
                lines.append(f"   - Expected: {step.expected_result}")

        return "\n".join(lines)


class GeneratedTestSuite(BaseModel):
    """Schema for AI-generated test suite."""
    test_cases: list[dict] = Field(description="List of generated test cases")
    coverage_summary: str = Field(description="Summary of what the tests cover")
    recommendations: list[str] = Field(description="Additional testing recommendations")


class TestGenerator:
    """
    Generates test cases from a flow graph using AI.
    Default provider is OpenAI for better test generation.
    """

    def __init__(
        self,
        provider: str = "openai",
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.provider = provider

        if provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.model = model or "gpt-4o"
            self.client = openai.OpenAI(api_key=self.api_key)
        elif provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            self.model = model or "claude-sonnet-4-20250514"
            self.client = Anthropic(api_key=self.api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def generate_test_cases(
        self,
        flow_graph: FlowGraph,
        test_types: list[TestType] | None = None,
        max_tests: int = 20,
        focus_areas: list[str] | None = None,
    ) -> list[TestCase]:
        """
        Generate test cases from a flow graph using AI.
        """
        test_types = test_types or list(TestType)

        # Prepare the graph summary for the AI
        graph_summary = self._prepare_graph_summary(flow_graph)

        prompt = self._build_prompt(graph_summary, test_types, max_tests, focus_areas)

        # Call AI to generate test cases
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8000,
            )
            response_text = response.choices[0].message.content
        else:  # anthropic
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.content[0].text

        # Parse the response
        test_cases = self._parse_ai_response(response_text)

        return test_cases

    def _prepare_graph_summary(self, flow_graph: FlowGraph) -> dict:
        """Prepare a summary of the flow graph for the AI."""
        return {
            "base_url": flow_graph.base_url,
            "total_pages": len(flow_graph.nodes),
            "total_transitions": len(flow_graph.edges),
            "pages": [
                {
                    "url": node.url,
                    "title": node.title,
                    "type": node.node_type,
                    "available_actions": node.available_actions[:10],  # Limit for token efficiency
                }
                for node in flow_graph.nodes.values()
            ],
            "transitions": [
                {
                    "from": edge.source_id,
                    "to": edge.target_id,
                    "type": edge.edge_type,
                    "action": edge.action,
                    "required_inputs": edge.required_inputs,
                }
                for edge in flow_graph.edges[:50]  # Limit for token efficiency
            ],
            "critical_paths": [
                [flow_graph.nodes[n].title for n in path if n in flow_graph.nodes]
                for path in flow_graph.get_critical_paths()[:5]
            ],
        }

    def _build_prompt(
        self,
        graph_summary: dict,
        test_types: list[TestType],
        max_tests: int,
        focus_areas: list[str] | None,
    ) -> str:
        """Build the prompt for test generation."""

        prompt = f"""You are an expert QA engineer. Analyze the following website structure and generate comprehensive test cases.

## Website Structure

```json
{json.dumps(graph_summary, indent=2)}
```

## Requirements

Generate up to {max_tests} test cases covering these test types:
{', '.join(t.value for t in test_types)}

{"Focus especially on: " + ', '.join(focus_areas) if focus_areas else ""}

## Output Format

Return a JSON object with this structure:
```json
{{
  "test_cases": [
    {{
      "id": "TC001",
      "name": "Test name",
      "description": "What this test verifies",
      "type": "happy_path|edge_case|error_handling|boundary|security|accessibility|performance",
      "priority": "critical|high|medium|low",
      "preconditions": ["User is logged out", "..."],
      "steps": [
        {{
          "order": 1,
          "action": "navigate|click|type|assert_visible|assert_text|assert_url|wait|screenshot",
          "target": "CSS selector or URL",
          "value": "Input value if applicable",
          "expected_result": "What should happen"
        }}
      ],
      "test_data": {{"email": "test@example.com", "password": "Test123!"}},
      "tags": ["login", "authentication"],
      "estimated_duration_seconds": 30
    }}
  ],
  "coverage_summary": "Summary of test coverage",
  "recommendations": ["Additional testing suggestions"]
}}
```

## Guidelines

1. **Happy Path Tests**: Cover the main user flows - signup, login, main features
2. **Edge Cases**: Empty inputs, special characters, very long inputs
3. **Error Handling**: Invalid inputs, network errors, unauthorized access
4. **Boundary Tests**: Min/max values, character limits
5. **Security**: XSS attempts, SQL injection patterns, authentication bypass
6. **Accessibility**: Keyboard navigation, screen reader compatibility
7. **Performance**: Page load times, response times for actions

For each form, generate at least:
- One happy path test with valid data
- One test with empty required fields
- One test with invalid data formats

Use realistic CSS selectors based on the element information provided.

Return ONLY the JSON object, no additional text."""

        return prompt

    def _parse_ai_response(self, response_text: str) -> list[TestCase]:
        """Parse the AI response into TestCase objects."""
        # Extract JSON from response
        try:
            # Try to find JSON in the response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response: {e}")
            print(f"Response: {response_text[:500]}...")
            return []

        test_cases = []
        for tc_data in data.get("test_cases", []):
            steps = [
                TestStep(
                    order=s.get("order", i + 1),
                    action=s.get("action", ""),
                    target=s.get("target", ""),
                    value=s.get("value"),
                    expected_result=s.get("expected_result"),
                    screenshot=s.get("screenshot", False),
                )
                for i, s in enumerate(tc_data.get("steps", []))
            ]

            test_case = TestCase(
                id=tc_data.get("id", f"TC{len(test_cases) + 1:03d}"),
                name=tc_data.get("name", "Unnamed Test"),
                description=tc_data.get("description", ""),
                test_type=TestType(tc_data.get("type", "happy_path")),
                priority=TestPriority(tc_data.get("priority", "medium")),
                steps=steps,
                preconditions=tc_data.get("preconditions", []),
                test_data=tc_data.get("test_data", {}),
                tags=tc_data.get("tags", []),
                estimated_duration_seconds=tc_data.get("estimated_duration_seconds", 30),
            )
            test_cases.append(test_case)

        return test_cases

    def generate_test_file(
        self,
        test_cases: list[TestCase],
        format: str = "playwright",
        output_path: str | None = None,
    ) -> str:
        """
        Generate a complete test file from test cases.
        """
        if format == "playwright":
            content = self._generate_playwright_file(test_cases)
        elif format == "natural":
            content = self._generate_natural_language_file(test_cases)
        elif format == "json":
            content = json.dumps([tc.to_dict() for tc in test_cases], indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

        if output_path:
            with open(output_path, "w") as f:
                f.write(content)

        return content

    def _generate_playwright_file(self, test_cases: list[TestCase]) -> str:
        """Generate a Playwright test file."""
        lines = [
            "import { test, expect } from '@playwright/test';",
            "",
            "// Auto-generated test cases",
            f"// Total tests: {len(test_cases)}",
            "",
        ]

        # Group by tags/features
        for tc in test_cases:
            lines.append("")
            lines.append(f"// {tc.description}")
            lines.append(f"// Priority: {tc.priority}, Type: {tc.test_type}")
            lines.append(tc.to_playwright())

        return "\n".join(lines)

    def _generate_natural_language_file(self, test_cases: list[TestCase]) -> str:
        """Generate a human-readable test plan."""
        lines = [
            "# Generated Test Plan",
            "",
            f"**Total Test Cases:** {len(test_cases)}",
            "",
            "---",
            "",
        ]

        for tc in test_cases:
            lines.append(tc.to_natural_language())
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)
