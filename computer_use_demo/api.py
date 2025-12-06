"""
FastAPI Backend for RoverQA
Replaces Streamlit with a proper REST API + WebSocket support.
"""

import asyncio
import base64
import json
import os
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from anthropic.types.beta import BetaTextBlockParam

from computer_use_demo.qa import (
    QACrawler,
    FlowGraphGenerator,
    TestGenerator,
    TestCase,
    TestType,
    TestPriority,
)
from computer_use_demo.loop import sampling_loop, APIProvider
from computer_use_demo.tools import ToolResult

# Load environment variables
load_dotenv()

app = FastAPI(
    title="RoverQA API",
    description="Crawl websites, generate flow graphs, and create test cases with AI",
    version="1.0.0",
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Models ==============

class CrawlRequest(BaseModel):
    url: str
    max_pages: int = Field(default=25, ge=1, le=100)
    max_depth: int = Field(default=3, ge=1, le=5)
    extract_structure: bool = False


class TestGenerationRequest(BaseModel):
    session_id: str
    test_types: list[str] = Field(default=["happy_path", "edge_case", "error_handling"])
    max_tests: int = Field(default=15, ge=1, le=50)
    ai_provider: str = Field(default="openai")


class TestExecutionRequest(BaseModel):
    session_id: str
    test_ids: list[str] | None = None  # None means all tests


class SessionState(BaseModel):
    id: str
    target_url: str | None = None
    crawl_result: dict | None = None
    flow_graph: dict | None = None
    test_cases: list[dict] = Field(default_factory=list)
    execution_status: str = "idle"
    created_at: datetime = Field(default_factory=datetime.now)


class APIKeyStatus(BaseModel):
    firecrawl: bool
    openai: bool
    anthropic: bool


# ============== Session Storage ==============

sessions: dict[str, dict] = {}


def get_session(session_id: str) -> dict:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


def create_session() -> str:
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "target_url": None,
        "crawl_result": None,
        "flow_graph": None,
        "test_cases": [],
        "execution_status": "idle",
        "messages": [],
        "tools": {},
        "created_at": datetime.now().isoformat(),
    }
    return session_id


# ============== API Endpoints ==============

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/keys/status", response_model=APIKeyStatus)
async def get_api_key_status():
    """Check which API keys are configured."""
    return APIKeyStatus(
        firecrawl=bool(os.getenv("FIRECRAWL_API_KEY")),
        openai=bool(os.getenv("OPENAI_API_KEY")),
        anthropic=bool(os.getenv("ANTHROPIC_API_KEY")),
    )


@app.post("/api/sessions")
async def create_new_session():
    """Create a new session."""
    session_id = create_session()
    return {"session_id": session_id}


@app.get("/api/sessions/{session_id}")
async def get_session_state(session_id: str):
    """Get current session state."""
    session = get_session(session_id)
    return {
        "id": session["id"],
        "target_url": session["target_url"],
        "has_crawl_result": session["crawl_result"] is not None,
        "has_flow_graph": session["flow_graph"] is not None,
        "test_count": len(session["test_cases"]),
        "execution_status": session["execution_status"],
        "created_at": session["created_at"],
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "deleted"}


@app.post("/api/crawl")
async def crawl_website(request: CrawlRequest):
    """Crawl a website and create a new session with the results."""
    session_id = create_session()
    session = sessions[session_id]
    session["target_url"] = request.url

    try:
        crawler = QACrawler()
        result = await crawler.crawl_site(
            url=request.url,
            max_pages=request.max_pages,
            max_depth=request.max_depth,
            extract_structure=request.extract_structure,
        )

        # Convert to serializable format
        crawl_data = {
            "base_url": result.base_url,
            "total_pages": result.total_pages,
            "pages": [
                {
                    "url": page.url,
                    "title": page.title,
                    "link_count": len(page.links),
                    "internal_links": page.links,  # Include actual links for transparency
                    "has_structure": page.structure is not None,
                    "forms_count": len(page.structure.forms) if page.structure else 0,
                    "buttons_count": len(page.structure.buttons) if page.structure else 0,
                    "inputs_count": len(page.structure.inputs) if page.structure else 0,
                    "links_count": len(page.structure.links) if page.structure else 0,
                }
                for page in result.pages
            ],
            "site_map": {k: v for k, v in result.site_map.items()},
            "all_discovered_links": list(set(
                link for links in result.site_map.values() for link in links
            )),
        }
        session["crawl_result"] = crawl_data

        # Generate flow graph
        generator = FlowGraphGenerator()
        flow_graph = generator.generate(result)
        session["flow_graph"] = flow_graph.to_dict()

        # Calculate stats
        total_links = sum(len(links) for links in result.site_map.values())
        forms_count = sum(
            1 for p in result.pages
            if p.structure and p.structure.forms
        )
        interactive_count = sum(
            len(p.structure.buttons) + len(p.structure.inputs) if p.structure else 0
            for p in result.pages
        )

        return {
            "session_id": session_id,
            "crawl_result": crawl_data,
            "flow_graph": session["flow_graph"],
            "stats": {
                "pages_found": result.total_pages,
                "total_links": total_links,
                "forms_found": forms_count,
                "interactive_elements": interactive_count,
                "nodes": len(flow_graph.nodes),
                "edges": len(flow_graph.edges),
                "critical_paths": len(flow_graph.get_critical_paths()),
            }
        }

    except Exception as e:
        # Clean up failed session
        del sessions[session_id]
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/crawl")
async def get_crawl_result(session_id: str):
    """Get crawl results for a session."""
    session = get_session(session_id)
    if not session["crawl_result"]:
        raise HTTPException(status_code=404, detail="No crawl result found")
    return session["crawl_result"]


@app.get("/api/sessions/{session_id}/flow-graph")
async def get_flow_graph(session_id: str):
    """Get flow graph for a session."""
    session = get_session(session_id)
    if not session["flow_graph"]:
        raise HTTPException(status_code=404, detail="No flow graph found")
    return session["flow_graph"]


@app.get("/api/sessions/{session_id}/flow-graph/mermaid")
async def get_flow_graph_mermaid(session_id: str):
    """Get flow graph as Mermaid diagram."""
    session = get_session(session_id)
    if not session["flow_graph"]:
        raise HTTPException(status_code=404, detail="No flow graph found")

    # Reconstruct mermaid from graph data
    graph_data = session["flow_graph"]
    lines = ["flowchart TD"]

    # Add nodes with better labels
    for node_id, node in graph_data.get("nodes", {}).items():
        safe_id = node_id.replace("-", "_").replace("/", "_").replace(".", "_").replace(" ", "_")
        title = node.get("title", "")
        url = node.get("url", "")

        # Create a clean label
        if title and title != url:
            label = title[:40] + "..." if len(title) > 40 else title
        else:
            # Extract from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path.strip('/') or "Home"
            label = path.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
            label = label[:40] if len(label) > 40 else label

        # Escape special characters for mermaid
        label = label.replace('"', "'").replace('[', '(').replace(']', ')')
        lines.append(f'    {safe_id}["{label}"]')

    # Add edges with action labels
    for edge in graph_data.get("edges", []):
        safe_source = edge["source"].replace("-", "_").replace("/", "_").replace(".", "_").replace(" ", "_")
        safe_target = edge["target"].replace("-", "_").replace("/", "_").replace(".", "_").replace(" ", "_")

        action = edge.get("action", "")
        edge_type = edge.get("type", "link")

        # Create a short label
        if action:
            label = action[:25] + "..." if len(action) > 25 else action
        else:
            label = edge_type

        label = label.replace('"', "'")
        lines.append(f'    {safe_source} -->|"{label}"| {safe_target}')

    return {"mermaid": "\n".join(lines)}


@app.post("/api/sessions/{session_id}/generate-tests")
async def generate_tests(session_id: str, request: TestGenerationRequest):
    """Generate test cases for a session."""
    session = get_session(session_id)

    if not session["flow_graph"]:
        raise HTTPException(status_code=400, detail="Flow graph required. Run crawl first.")

    try:
        # We need to reconstruct the FlowGraph object from the stored dict
        from computer_use_demo.qa.flow_graph import FlowGraph, Node, Edge, EdgeType, NodeType

        graph_data = session["flow_graph"]
        flow_graph = FlowGraph(base_url=graph_data["base_url"])

        for node_id, node_data in graph_data.get("nodes", {}).items():
            node = Node(
                id=node_data["id"],
                url=node_data["url"],
                title=node_data["title"],
                node_type=NodeType(node_data.get("type", "page")),
                available_actions=node_data.get("actions", []),
                metadata=node_data.get("metadata", {}),
            )
            flow_graph.add_node(node)

        for edge_data in graph_data.get("edges", []):
            edge = Edge(
                id=edge_data["id"],
                source_id=edge_data["source"],
                target_id=edge_data["target"],
                edge_type=EdgeType(edge_data.get("type", "link")),
                action=edge_data.get("action", ""),
                required_inputs=edge_data.get("required_inputs", []),
                preconditions=edge_data.get("preconditions", []),
            )
            flow_graph.add_edge(edge)

        flow_graph.entry_points = graph_data.get("entry_points", [])

        # Generate tests
        generator = TestGenerator(provider=request.ai_provider)
        test_types = [TestType(t) for t in request.test_types]
        tests = await generator.generate_test_cases(
            flow_graph=flow_graph,
            test_types=test_types,
            max_tests=request.max_tests,
        )

        # Store tests
        session["test_cases"] = [t.to_dict() for t in tests]

        # Generate Playwright code
        playwright_code = "\n\n".join(t.to_playwright() for t in tests)

        return {
            "test_count": len(tests),
            "tests": session["test_cases"],
            "playwright_code": playwright_code,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/tests")
async def get_tests(session_id: str, priority: str | None = None):
    """Get generated test cases."""
    session = get_session(session_id)
    tests = session["test_cases"]

    if priority:
        tests = [t for t in tests if t.get("priority") == priority]

    return {"tests": tests, "total": len(tests)}


@app.get("/api/sessions/{session_id}/tests/export/{format}")
async def export_tests(session_id: str, format: str):
    """Export tests in various formats."""
    session = get_session(session_id)
    tests = session["test_cases"]

    if not tests:
        raise HTTPException(status_code=404, detail="No tests found")

    if format == "json":
        return {"content": json.dumps(tests, indent=2), "filename": "test_cases.json"}
    elif format == "playwright":
        # Reconstruct TestCase objects for Playwright generation
        from computer_use_demo.qa.test_generator import TestCase, TestStep

        test_objs = []
        for t in tests:
            steps = [
                TestStep(
                    order=s.get("order", i + 1),
                    action=s.get("action", ""),
                    target=s.get("target", ""),
                    value=s.get("value"),
                    expected_result=s.get("expected_result"),
                )
                for i, s in enumerate(t.get("steps", []))
            ]
            tc = TestCase(
                id=t.get("id", ""),
                name=t.get("name", ""),
                description=t.get("description", ""),
                test_type=TestType(t.get("type", "happy_path")),
                priority=TestPriority(t.get("priority", "medium")),
                steps=steps,
                preconditions=t.get("preconditions", []),
                test_data=t.get("test_data", {}),
                tags=t.get("tags", []),
            )
            test_objs.append(tc)

        code = "import { test, expect } from '@playwright/test';\n\n"
        code += "\n\n".join(tc.to_playwright() for tc in test_objs)
        return {"content": code, "filename": "generated_tests.spec.ts"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown format: {format}")


# ============== WebSocket for Test Execution ==============

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)


manager = ConnectionManager()


def build_test_execution_prompt(test_cases: list[dict], base_url: str) -> str:
    """Build the prompt for executing test cases."""
    test_descriptions = []
    for tc in test_cases:
        steps_text = "\n".join([
            f"  {step.get('order', i+1)}. {step.get('action', '').upper()}: {step.get('target', '')}"
            + (f" (value: {step.get('value')})" if step.get('value') else "")
            + (f" [Expected: {step.get('expected_result')}]" if step.get('expected_result') else "")
            for i, step in enumerate(tc.get("steps", []))
        ])
        test_descriptions.append(f"""
### Test: {tc.get('id')} - {tc.get('name')}
**Type:** {tc.get('type')} | **Priority:** {tc.get('priority')}
**Description:** {tc.get('description')}
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


@app.websocket("/ws/execute/{session_id}")
async def websocket_execute_tests(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time test execution."""
    await manager.connect(websocket, session_id)

    try:
        session = get_session(session_id)
        session["execution_status"] = "running"

        # Send initial status
        await manager.send_message(session_id, {
            "type": "status",
            "status": "starting",
            "message": "Starting test execution...",
        })

        test_cases = session["test_cases"]
        base_url = session["target_url"]

        if not base_url:
            await manager.send_message(session_id, {
                "type": "error",
                "message": "No target URL found. Please crawl a website first.",
            })
            session["execution_status"] = "error"
            return

        if not test_cases:
            await manager.send_message(session_id, {
                "type": "error",
                "message": "No test cases found. Please generate tests first.",
            })
            session["execution_status"] = "error"
            return

        await manager.send_message(session_id, {
            "type": "status",
            "status": "running",
            "message": f"Executing {len(test_cases)} test cases on {base_url}",
        })

        # Build the prompt
        prompt = build_test_execution_prompt(test_cases, base_url)

        messages = [{
            "role": "user",
            "content": [BetaTextBlockParam(type="text", text=prompt)],
        }]

        api_key = os.getenv("ANTHROPIC_API_KEY")

        # Output callback to send messages to WebSocket
        async def output_callback(content):
            if isinstance(content, dict):
                if content.get("type") == "text":
                    await manager.send_message(session_id, {
                        "type": "message",
                        "role": "assistant",
                        "content": content.get("text", ""),
                    })
                elif content.get("type") == "tool_use":
                    await manager.send_message(session_id, {
                        "type": "tool_use",
                        "name": content.get("name", ""),
                        "input": content.get("input", {}),
                    })
            elif isinstance(content, str):
                await manager.send_message(session_id, {
                    "type": "message",
                    "role": "assistant",
                    "content": content,
                })

        # Tool output callback
        tool_state = {}

        async def tool_output_callback(tool_output: ToolResult, tool_id: str):
            tool_state[tool_id] = tool_output
            msg = {
                "type": "tool_result",
                "tool_id": tool_id,
            }
            if tool_output.output:
                msg["output"] = tool_output.output
            if tool_output.error:
                msg["error"] = tool_output.error
            if tool_output.base64_image:
                msg["screenshot"] = tool_output.base64_image
            await manager.send_message(session_id, msg)

        # API response callback
        response_state = {}

        def api_response_callback(request, response, error):
            response_id = datetime.now().isoformat()
            response_state[response_id] = (request, response)
            if error:
                asyncio.create_task(manager.send_message(session_id, {
                    "type": "error",
                    "message": str(error),
                }))

        # Run the sampling loop
        try:
            messages = await sampling_loop(
                system_prompt_suffix="You are executing automated QA tests. Be thorough and report results clearly.",
                model="claude-sonnet-4-20250514",
                provider=APIProvider.ANTHROPIC,
                messages=messages,
                output_callback=output_callback,
                tool_output_callback=tool_output_callback,
                api_response_callback=api_response_callback,
                api_key=api_key,
                only_n_most_recent_images=3,
                tool_version="computer_use_20250124",
                max_tokens=16000,
            )

            session["execution_status"] = "complete"
            await manager.send_message(session_id, {
                "type": "status",
                "status": "complete",
                "message": "Test execution completed",
            })

        except Exception as e:
            session["execution_status"] = "error"
            await manager.send_message(session_id, {
                "type": "error",
                "message": str(e),
            })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        if session_id in sessions:
            sessions[session_id]["execution_status"] = "disconnected"
    finally:
        manager.disconnect(session_id)


# ============== Static File Serving (for production) ==============

def get_frontend_path():
    """Find the frontend build directory."""
    # Try multiple possible locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"),  # Local dev
        os.path.join(os.path.expanduser("~"), "frontend", "dist"),  # Docker
        "/home/computeruse/frontend/dist",  # Docker explicit
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

frontend_build_path = get_frontend_path()
if frontend_build_path:
    assets_path = os.path.join(frontend_build_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_build_path, "index.html"))

    @app.get("/{path:path}")
    async def serve_frontend_routes(path: str):
        # Don't intercept API routes
        if path.startswith("api/") or path.startswith("ws/"):
            raise HTTPException(status_code=404)
        # Serve index.html for client-side routing
        file_path = os.path.join(frontend_build_path, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_build_path, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
