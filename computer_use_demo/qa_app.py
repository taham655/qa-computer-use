"""
RoverQA - Streamlit Application
Crawl websites, generate flow graphs, create test cases using AI, and execute them with computer-use agent.
"""

import asyncio
import base64
import json
import os
from datetime import datetime
from enum import StrEnum
from functools import partial
from typing import cast

import httpx
import streamlit as st
from dotenv import load_dotenv
from anthropic.types.beta import BetaContentBlockParam, BetaTextBlockParam

from computer_use_demo.qa import (
    QACrawler,
    FlowGraphGenerator,
    TestGenerator,
    TestCase,
    TestType,
)
from computer_use_demo.loop import sampling_loop, APIProvider
from computer_use_demo.tools import ToolResult

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="RoverQA",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a modern look
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-tertiary: #1a1a26;
        --accent-cyan: #00d4ff;
        --accent-magenta: #ff0080;
        --accent-yellow: #ffd000;
        --text-primary: #e8e8f0;
        --text-secondary: #9090a0;
        --border-color: #2a2a3a;
    }

    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    }

    .main-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-magenta));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .sub-header {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    .stat-card {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }

    .stat-card:hover {
        border-color: var(--accent-cyan);
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
    }

    .stat-number {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 600;
        color: var(--accent-cyan);
    }

    .stat-label {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--text-secondary);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .test-card {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .test-card:hover {
        border-color: var(--accent-magenta);
    }

    .priority-critical { color: #ff4444; }
    .priority-high { color: #ff8800; }
    .priority-medium { color: var(--accent-yellow); }
    .priority-low { color: #44ff44; }

    .step-badge {
        display: inline-block;
        background: var(--accent-cyan);
        color: var(--bg-primary);
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .mermaid-container {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 2rem;
        overflow-x: auto;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom button styling */
    .stButton > button {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
    }

    /* Code blocks */
    code {
        font-family: 'JetBrains Mono', monospace !important;
    }
</style>
"""


class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"


def setup_state():
    """Initialize session state variables."""
    if "crawl_result" not in st.session_state:
        st.session_state.crawl_result = None
    if "flow_graph" not in st.session_state:
        st.session_state.flow_graph = None
    if "test_cases" not in st.session_state:
        st.session_state.test_cases = []
    if "crawl_status" not in st.session_state:
        st.session_state.crawl_status = "idle"
    if "selected_test" not in st.session_state:
        st.session_state.selected_test = None
    # Execution state
    if "execution_results" not in st.session_state:
        st.session_state.execution_results = None
    if "execution_status" not in st.session_state:
        st.session_state.execution_status = "idle"  # idle, running, complete
    if "current_test_index" not in st.session_state:
        st.session_state.current_test_index = 0
    if "target_url" not in st.session_state:
        st.session_state.target_url = ""
    # Execution view state (like original demo)
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "setup"  # setup, execution
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "tools" not in st.session_state:
        st.session_state.tools = {}
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if "in_sampling_loop" not in st.session_state:
        st.session_state.in_sampling_loop = False
    if "hide_images" not in st.session_state:
        st.session_state.hide_images = False


def render_header():
    """Render the main header."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">🧪 RoverQA</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Crawl websites, generate flow graphs, and create comprehensive test cases with AI</p>',
        unsafe_allow_html=True
    )


def render_sidebar():
    """Render the sidebar with configuration options."""
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")

        # API Keys status
        st.markdown("#### API Keys")
        firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        col1, col2 = st.columns(2)
        with col1:
            if firecrawl_key:
                st.success("Firecrawl ✓")
            else:
                st.error("Firecrawl ✗")
        with col2:
            if openai_key:
                st.success("OpenAI ✓")
            elif anthropic_key:
                st.success("Anthropic ✓")
            else:
                st.error("AI API ✗")

        st.markdown("---")

        # Crawl settings
        st.markdown("#### Crawl Settings")
        max_pages = st.slider("Max Pages", 5, 100, 25, help="Maximum pages to crawl")
        max_depth = st.slider("Max Depth", 1, 5, 3, help="Maximum crawl depth")
        extract_structure = st.checkbox("Extract Page Structure", value=False, help="Use AI to extract interactive elements (slower)")

        st.markdown("---")

        # Test generation settings
        st.markdown("#### Test Generation")
        test_types = st.multiselect(
            "Test Types",
            options=[t.value for t in TestType],
            default=["happy_path", "edge_case", "error_handling"],
        )
        max_tests = st.slider("Max Tests", 5, 50, 15)

        # OpenAI is now the default provider (index=0)
        ai_provider = st.selectbox("AI Provider", ["openai", "anthropic"], index=0)

        st.markdown("---")

        # Reset button
        if st.button("🔄 Reset All", type="secondary"):
            st.session_state.crawl_result = None
            st.session_state.flow_graph = None
            st.session_state.test_cases = []
            st.session_state.crawl_status = "idle"
            st.session_state.execution_results = None
            st.session_state.execution_status = "idle"
            st.session_state.current_test_index = 0
            st.session_state.view_mode = "setup"
            st.session_state.messages = []
            st.session_state.tools = {}
            st.rerun()

        # Back to setup button (when in execution mode)
        if st.session_state.view_mode == "execution":
            if st.button("⬅️ Back to Setup", type="secondary"):
                st.session_state.view_mode = "setup"
                st.rerun()

        return {
            "max_pages": max_pages,
            "max_depth": max_depth,
            "extract_structure": extract_structure,
            "test_types": [TestType(t) for t in test_types],
            "max_tests": max_tests,
            "ai_provider": ai_provider,
        }


def render_url_input():
    """Render the URL input section."""
    st.markdown("### 🔗 Enter URL to Test")

    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input(
            "URL",
            placeholder="https://example.com",
            label_visibility="collapsed",
        )
    with col2:
        crawl_button = st.button("🚀 Start Crawl", type="primary", use_container_width=True)

    return url, crawl_button


async def run_crawl(url: str, settings: dict):
    """Run the crawl operation."""
    try:
        crawler = QACrawler()
        result = await crawler.crawl_site(
            url=url,
            max_pages=settings["max_pages"],
            max_depth=settings["max_depth"],
            extract_structure=settings["extract_structure"],
        )
        return result
    except Exception as e:
        st.error(f"Crawl failed: {str(e)}")
        return None


def render_crawl_results():
    """Render the crawl results section."""
    if not st.session_state.crawl_result:
        return

    result = st.session_state.crawl_result

    st.markdown("### 📊 Crawl Results")

    # Stats cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""<div class="stat-card">
                <div class="stat-number">{result.total_pages}</div>
                <div class="stat-label">Pages Found</div>
            </div>""",
            unsafe_allow_html=True
        )

    with col2:
        total_links = sum(len(links) for links in result.site_map.values())
        st.markdown(
            f"""<div class="stat-card">
                <div class="stat-number">{total_links}</div>
                <div class="stat-label">Total Links</div>
            </div>""",
            unsafe_allow_html=True
        )

    with col3:
        forms_count = sum(
            1 for p in result.pages
            if p.structure and p.structure.forms
        )
        st.markdown(
            f"""<div class="stat-card">
                <div class="stat-number">{forms_count}</div>
                <div class="stat-label">Forms Found</div>
            </div>""",
            unsafe_allow_html=True
        )

    with col4:
        interactive_count = sum(
            len(p.structure.buttons) + len(p.structure.inputs) if p.structure else 0
            for p in result.pages
        )
        st.markdown(
            f"""<div class="stat-card">
                <div class="stat-number">{interactive_count}</div>
                <div class="stat-label">Interactive Elements</div>
            </div>""",
            unsafe_allow_html=True
        )

    # Pages list
    with st.expander("📄 Pages Discovered", expanded=False):
        for page in result.pages:
            st.markdown(f"**{page.title or 'Untitled'}**")
            st.caption(page.url)
            if page.structure:
                st.caption(
                    f"🔘 {len(page.structure.buttons)} buttons • "
                    f"📝 {len(page.structure.forms)} forms • "
                    f"🔗 {len(page.structure.links)} links"
                )
            st.markdown("---")


def render_flow_graph():
    """Render the flow graph section."""
    if not st.session_state.flow_graph:
        return

    graph = st.session_state.flow_graph

    st.markdown("### 🔀 Flow Graph")

    # Graph stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nodes", len(graph.nodes))
    with col2:
        st.metric("Edges", len(graph.edges))
    with col3:
        critical_paths = graph.get_critical_paths()
        st.metric("Critical Paths", len(critical_paths))

    # Mermaid diagram
    with st.expander("📈 Visual Graph (Mermaid)", expanded=True):
        mermaid_code = graph.to_mermaid()
        st.code(mermaid_code, language="mermaid")

    # JSON export
    with st.expander("📦 Graph JSON", expanded=False):
        st.json(graph.to_dict())


def render_test_cases():
    """Render the generated test cases."""
    if not st.session_state.test_cases:
        return

    tests = st.session_state.test_cases

    st.markdown("### 🧪 Generated Test Cases")
    st.caption(f"{len(tests)} test cases generated")

    # Filter by priority
    priorities = st.multiselect(
        "Filter by Priority",
        ["critical", "high", "medium", "low"],
        default=["critical", "high", "medium", "low"],
    )

    filtered_tests = [t for t in tests if t.priority in priorities]

    # Test cards
    for test in filtered_tests:
        priority_class = f"priority-{test.priority}"

        with st.expander(f"**{test.id}**: {test.name}", expanded=False):
            st.markdown(f"**Type:** {test.test_type} | **Priority:** :{priority_class}[{test.priority}]")
            st.markdown(f"**Description:** {test.description}")

            if test.preconditions:
                st.markdown("**Preconditions:**")
                for pre in test.preconditions:
                    st.markdown(f"- {pre}")

            st.markdown("**Steps:**")
            for step in test.steps:
                st.markdown(
                    f"{step.order}. `{step.action}` → `{step.target}`"
                    + (f" with `{step.value}`" if step.value else "")
                )
                if step.expected_result:
                    st.caption(f"   Expected: {step.expected_result}")

            if test.test_data:
                st.markdown("**Test Data:**")
                st.json(test.test_data)

            # Show Playwright code
            st.markdown("**Playwright Code:**")
            st.code(test.to_playwright(), language="typescript")

    # Export buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        playwright_code = "\n\n".join(t.to_playwright() for t in tests)
        st.download_button(
            "📥 Download Playwright",
            playwright_code,
            "generated_tests.spec.ts",
            "text/typescript",
        )

    with col2:
        json_data = json.dumps([t.to_dict() for t in tests], indent=2)
        st.download_button(
            "📥 Download JSON",
            json_data,
            "test_cases.json",
            "application/json",
        )

    with col3:
        natural_lang = "\n\n---\n\n".join(t.to_natural_language() for t in tests)
        st.download_button(
            "📥 Download Test Plan",
            natural_lang,
            "test_plan.md",
            "text/markdown",
        )


async def generate_tests(settings: dict):
    """Generate test cases from the flow graph."""
    if not st.session_state.flow_graph:
        st.error("Please generate a flow graph first")
        return

    generator = TestGenerator(provider=settings["ai_provider"])
    tests = await generator.generate_test_cases(
        flow_graph=st.session_state.flow_graph,
        test_types=settings["test_types"],
        max_tests=settings["max_tests"],
    )

    return tests


def _render_message(sender: Sender, message: str | BetaContentBlockParam | ToolResult):
    """Render a message in the chat interface."""
    is_tool_result = not isinstance(message, str | dict)
    if not message or (
        is_tool_result
        and st.session_state.hide_images
        and not hasattr(message, "error")
        and not hasattr(message, "output")
    ):
        return

    with st.chat_message(sender):
        if is_tool_result:
            message = cast(ToolResult, message)
            if message.output:
                if message.__class__.__name__ == "CLIResult":
                    st.code(message.output)
                else:
                    st.markdown(message.output)
            if message.error:
                st.error(message.error)
            if message.base64_image and not st.session_state.hide_images:
                st.image(base64.b64decode(message.base64_image))
        elif isinstance(message, dict):
            if message["type"] == "text":
                st.write(message["text"])
            elif message["type"] == "thinking":
                st.markdown(f"[Thinking]\n\n{message.get('thinking', '')}")
            elif message["type"] == "tool_use":
                st.code(f"Tool Use: {message['name']}\nInput: {message['input']}")
        else:
            st.markdown(message)


def _tool_output_callback(tool_output: ToolResult, tool_id: str, tool_state: dict):
    """Handle a tool output."""
    tool_state[tool_id] = tool_output
    _render_message(Sender.TOOL, tool_output)


def _api_response_callback(
    request: httpx.Request,
    response: httpx.Response | object | None,
    error: Exception | None,
    tab,
    response_state: dict,
):
    """Handle API response."""
    response_id = datetime.now().isoformat()
    response_state[response_id] = (request, response)
    if error:
        st.error(f"API Error: {error}")


def build_test_execution_prompt(test_cases: list[TestCase], base_url: str) -> str:
    """Build the prompt for executing test cases."""
    test_descriptions = []
    for tc in test_cases:
        steps_text = "\n".join([
            f"  {step.order}. {step.action.upper()}: {step.target}"
            + (f" (value: {step.value})" if step.value else "")
            + (f" [Expected: {step.expected_result}]" if step.expected_result else "")
            for step in tc.steps
        ])
        test_descriptions.append(f"""
### Test: {tc.id} - {tc.name}
**Type:** {tc.test_type} | **Priority:** {tc.priority}
**Description:** {tc.description}
**Steps:**
{steps_text}
""")

    return f"""You are a QA automation agent. Execute the following test cases on {base_url} using the computer tools.

## Test Cases to Execute:
{"".join(test_descriptions)}

## Instructions:
1. Open Firefox and navigate to {base_url}
2. Execute each test case in order
3. For each test:
   - Follow the steps exactly as described
   - Verify expected results after each action
   - Take screenshots at key moments
   - Report PASS or FAIL for each test with explanation
4. After completing all tests, provide a summary of results

## Important:
- Use the `computer` tool to interact with the screen
- Click on elements, type text, and navigate as needed
- Wait for pages to load before interacting
- If an element is not visible, try scrolling
- Be thorough and report any issues found

Begin executing the tests now. Start by opening Firefox."""


async def run_test_execution():
    """Run the test execution using the sampling loop."""
    test_cases = st.session_state.test_cases
    base_url = st.session_state.target_url

    # Build the initial prompt
    prompt = build_test_execution_prompt(test_cases, base_url)

    # Add the initial message
    st.session_state.messages.append({
        "role": Sender.USER,
        "content": [BetaTextBlockParam(type="text", text=prompt)],
    })

    # Run the sampling loop
    st.session_state.in_sampling_loop = True
    try:
        st.session_state.messages = await sampling_loop(
            system_prompt_suffix="You are executing automated QA tests. Be thorough and report results clearly.",
            model="claude-sonnet-4-20250514",
            provider=APIProvider.ANTHROPIC,
            messages=st.session_state.messages,
            output_callback=partial(_render_message, Sender.BOT),
            tool_output_callback=partial(_tool_output_callback, tool_state=st.session_state.tools),
            api_response_callback=partial(
                _api_response_callback,
                tab=None,
                response_state=st.session_state.responses,
            ),
            api_key=st.session_state.api_key,
            only_n_most_recent_images=3,
            tool_version="computer_use_20250124",
            max_tokens=16000,
        )
        st.session_state.execution_status = "complete"
    except Exception as e:
        st.error(f"Execution error: {e}")
        st.session_state.execution_status = "error"
    finally:
        st.session_state.in_sampling_loop = False


def render_execution_view():
    """Render the execution view with agent messages."""
    st.markdown("### 🤖 Test Execution")

    # Show test summary
    test_cases = st.session_state.test_cases
    st.info(f"Executing {len(test_cases)} test cases on {st.session_state.target_url}")

    # Progress indicator
    if st.session_state.execution_status == "running":
        st.markdown("🔄 **Status:** Running...")
    elif st.session_state.execution_status == "complete":
        st.success("✅ **Status:** Execution Complete")
    elif st.session_state.execution_status == "error":
        st.error("❌ **Status:** Execution Failed")

    st.markdown("---")

    # Render past messages
    for message in st.session_state.messages:
        if isinstance(message["content"], str):
            _render_message(message["role"], message["content"])
        elif isinstance(message["content"], list):
            for block in message["content"]:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tool_id = block.get("tool_use_id")
                    if tool_id and tool_id in st.session_state.tools:
                        _render_message(Sender.TOOL, st.session_state.tools[tool_id])
                else:
                    _render_message(message["role"], cast(BetaContentBlockParam | ToolResult, block))


async def main():
    """Main application entry point."""
    setup_state()
    render_header()
    settings = render_sidebar()

    # Check which view mode we're in
    if st.session_state.view_mode == "execution":
        # Execution view - show agent messages
        render_execution_view()

        # If execution hasn't started yet, start it
        if st.session_state.execution_status == "idle" and st.session_state.test_cases:
            st.session_state.execution_status = "running"
            await run_test_execution()
            st.rerun()

        return

    # Setup view - show crawl, generate, test cases
    url, crawl_clicked = render_url_input()

    # Handle crawl button
    if crawl_clicked and url:
        st.session_state.target_url = url

        with st.spinner("🔍 Crawling website..."):
            result = await run_crawl(url, settings)
            if result:
                st.session_state.crawl_result = result

                with st.spinner("🔀 Generating flow graph..."):
                    generator = FlowGraphGenerator()
                    st.session_state.flow_graph = generator.generate(result)

                st.success("✅ Crawl complete!")
                st.rerun()

    # Render results
    render_crawl_results()
    render_flow_graph()

    # Generate tests button
    if st.session_state.flow_graph and not st.session_state.test_cases:
        st.markdown("---")
        if st.button("🤖 Generate Test Cases with AI", type="primary", use_container_width=True):
            with st.spinner("🧠 AI is generating test cases..."):
                tests = await generate_tests(settings)
                if tests:
                    st.session_state.test_cases = tests
                    st.success(f"✅ Generated {len(tests)} test cases!")
                    st.rerun()

    render_test_cases()

    # Execute tests button - switches to execution view
    if st.session_state.test_cases:
        st.markdown("---")
        st.markdown("### 🚀 Execute Tests")
        st.info("Click the button below to start executing tests. The agent will use the computer-use tools to interact with the browser and run all test cases.")

        if st.button("🤖 Execute Tests with Computer-Use Agent", type="primary", use_container_width=True):
            # Reset execution state
            st.session_state.messages = []
            st.session_state.tools = {}
            st.session_state.execution_status = "idle"
            st.session_state.view_mode = "execution"
            st.rerun()


if __name__ == "__main__":
    asyncio.run(main())
