"""
Flow Graph Generator - Creates a directed graph of user flows from crawled website data.
"""

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse, urljoin, urlunparse

from .crawler import CrawlResult, PageData, InteractiveElement, FormData


def normalize_url(url: str, base_url: str | None = None) -> str:
    """
    Normalize a URL for consistent comparison.
    - Remove trailing slashes
    - Remove fragments
    - Remove common tracking params
    - Convert to lowercase domain
    """
    if not url:
        return ""

    # Handle relative URLs
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)

    try:
        parsed = urlparse(url)
        # Lowercase the domain
        netloc = parsed.netloc.lower()
        # Remove trailing slash from path
        path = parsed.path.rstrip('/') or '/'
        # Rebuild without fragment
        normalized = urlunparse((
            parsed.scheme.lower(),
            netloc,
            path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        return normalized
    except Exception:
        return url


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs are from the same domain."""
    try:
        domain1 = urlparse(url1).netloc.lower().replace('www.', '')
        domain2 = urlparse(url2).netloc.lower().replace('www.', '')
        return domain1 == domain2
    except Exception:
        return False


def extract_domain(url: str) -> str:
    """Extract the domain from a URL."""
    try:
        return urlparse(url).netloc.lower().replace('www.', '')
    except Exception:
        return ""


class EdgeType(StrEnum):
    """Types of transitions between pages/states."""
    NAVIGATION = "navigation"  # Click on nav link
    LINK = "link"              # Click on any link
    FORM_SUBMIT = "form_submit"  # Submit a form
    BUTTON_CLICK = "button_click"  # Click a button
    MODAL_OPEN = "modal_open"  # Open a modal
    MODAL_CLOSE = "modal_close"  # Close a modal
    DROPDOWN_SELECT = "dropdown_select"  # Select from dropdown
    INPUT = "input"  # Fill an input field


class NodeType(StrEnum):
    """Types of nodes in the flow graph."""
    PAGE = "page"  # A full page
    MODAL = "modal"  # A modal/popup state
    FORM_STATE = "form_state"  # Form with specific state
    ERROR_STATE = "error_state"  # Error page/state
    SUCCESS_STATE = "success_state"  # Success confirmation


@dataclass
class Node:
    """A node in the flow graph representing a page or state."""
    id: str
    url: str
    title: str
    node_type: NodeType = NodeType.PAGE
    page_data: PageData | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Interactive elements available on this node
    available_actions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "type": self.node_type,
            "actions": self.available_actions,
            "metadata": self.metadata,
        }


@dataclass
class Edge:
    """An edge in the flow graph representing a user action/transition."""
    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    action: str  # Description of the action
    element: InteractiveElement | None = None
    required_inputs: list[dict[str, Any]] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type,
            "action": self.action,
            "required_inputs": self.required_inputs,
            "preconditions": self.preconditions,
        }


@dataclass
class FlowGraph:
    """
    Directed graph representing all possible user flows through a website.
    """
    base_url: str
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)  # Node IDs that are entry points

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)

    def get_outgoing_edges(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.source_id == node_id]

    def get_incoming_edges(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.target_id == node_id]

    def get_all_paths(self, max_depth: int = 10) -> list[list[str]]:
        """Get all possible paths through the graph up to max_depth."""
        paths = []

        def dfs(current_id: str, path: list[str], depth: int):
            if depth >= max_depth:
                paths.append(path.copy())
                return

            outgoing = self.get_outgoing_edges(current_id)
            if not outgoing:
                paths.append(path.copy())
                return

            for edge in outgoing:
                if edge.target_id not in path:  # Avoid cycles
                    path.append(edge.target_id)
                    dfs(edge.target_id, path, depth + 1)
                    path.pop()

        for entry in self.entry_points:
            dfs(entry, [entry], 0)

        return paths

    def get_critical_paths(self) -> list[list[str]]:
        """
        Identify critical user paths (e.g., signup, checkout, main features).
        These are paths that contain form submissions or key actions.
        """
        critical = []
        for path in self.get_all_paths():
            edges_in_path = []
            for i in range(len(path) - 1):
                edges_in_path.extend([
                    e for e in self.edges
                    if e.source_id == path[i] and e.target_id == path[i + 1]
                ])

            # Path is critical if it contains form submissions
            if any(e.edge_type == EdgeType.FORM_SUBMIT for e in edges_in_path):
                critical.append(path)

        return critical

    def to_dict(self) -> dict:
        return {
            "base_url": self.base_url,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "entry_points": self.entry_points,
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "total_paths": len(self.get_all_paths(max_depth=5)),
            }
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram syntax for visualization."""
        lines = ["flowchart TD"]

        # Add nodes with safe IDs
        for node_id, node in self.nodes.items():
            safe_id = self._make_safe_mermaid_id(node_id)

            # Create a clean label
            if node.title and node.title != node.url:
                label = node.title[:40] + "..." if len(node.title) > 40 else node.title
            else:
                parsed = urlparse(node.url)
                path = parsed.path.strip('/') or "Home"
                label = path.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
                label = label[:40] if len(label) > 40 else label

            # Escape special characters
            label = label.replace('"', "'").replace('[', '(').replace(']', ')')
            lines.append(f'    {safe_id}["{label}"]')

        # Add edges
        for edge in self.edges:
            safe_source = self._make_safe_mermaid_id(edge.source_id)
            safe_target = self._make_safe_mermaid_id(edge.target_id)

            action = edge.action[:25] + "..." if len(edge.action) > 25 else edge.action
            action = action.replace('"', "'")
            lines.append(f'    {safe_source} -->|"{action}"| {safe_target}')

        return "\n".join(lines)

    def _make_safe_mermaid_id(self, node_id: str) -> str:
        """Convert a node ID to a safe mermaid identifier."""
        return node_id.replace("-", "_").replace("/", "_").replace(".", "_").replace(" ", "_").replace(":", "_")


class FlowGraphGenerator:
    """
    Generates a flow graph from crawled website data.
    """

    def __init__(self):
        self._node_counter = 0
        self._edge_counter = 0
        self._added_edges: set[tuple[str, str]] = set()  # Track (source, target) pairs

    def _generate_node_id(self, url: str) -> str:
        """Generate a unique node ID from URL."""
        parsed = urlparse(url)
        path = parsed.path.strip("/") or "home"
        # Clean path for ID
        clean_path = path.replace('/', '_').replace('.', '_').replace('-', '_')
        return f"{clean_path}_{self._node_counter}"

    def _generate_edge_id(self) -> str:
        self._edge_counter += 1
        return f"edge_{self._edge_counter}"

    def generate(self, crawl_result: CrawlResult) -> FlowGraph:
        """
        Generate a flow graph from crawl results with proper URL normalization.
        """
        graph = FlowGraph(base_url=crawl_result.base_url)
        base_domain = extract_domain(crawl_result.base_url)

        # Build normalized URL to node ID mapping
        url_to_node_id: dict[str, str] = {}
        normalized_to_original: dict[str, str] = {}

        # First pass: Create nodes for each crawled page
        for page in crawl_result.pages:
            self._node_counter += 1
            node_id = self._generate_node_id(page.url)

            # Store both original and normalized URLs
            normalized_url = normalize_url(page.url)
            url_to_node_id[page.url] = node_id
            url_to_node_id[normalized_url] = node_id
            normalized_to_original[normalized_url] = page.url

            # Extract available actions from page structure
            actions = self._extract_actions(page)

            node = Node(
                id=node_id,
                url=page.url,
                title=page.title or self._extract_title_from_url(page.url),
                node_type=self._determine_node_type(page),
                page_data=page,
                available_actions=actions,
                metadata={
                    "has_forms": bool(page.structure and page.structure.forms),
                    "link_count": len(page.links),
                    "internal_links": sum(1 for link in page.links if is_same_domain(link, crawl_result.base_url)),
                }
            )
            graph.add_node(node)

        # Set entry point (base URL)
        base_normalized = normalize_url(crawl_result.base_url)
        if base_normalized in url_to_node_id:
            graph.entry_points.append(url_to_node_id[base_normalized])
        elif crawl_result.base_url in url_to_node_id:
            graph.entry_points.append(url_to_node_id[crawl_result.base_url])
        elif url_to_node_id:
            graph.entry_points.append(list(url_to_node_id.values())[0])

        # Reset edge tracking
        self._added_edges = set()

        # Second pass: Create edges based on links
        for page in crawl_result.pages:
            source_id = url_to_node_id.get(page.url) or url_to_node_id.get(normalize_url(page.url))
            if not source_id:
                continue

            # Process all links from the page
            for link_url in page.links:
                # Skip external links
                if not is_same_domain(link_url, crawl_result.base_url):
                    continue

                # Normalize the link URL
                normalized_link = normalize_url(link_url, crawl_result.base_url)

                # Try to find the target node
                target_id = url_to_node_id.get(normalized_link) or url_to_node_id.get(link_url)

                if target_id and target_id != source_id:
                    # Check if we already added this edge
                    edge_key = (source_id, target_id)
                    if edge_key not in self._added_edges:
                        self._added_edges.add(edge_key)

                        # Determine edge type based on link text analysis
                        edge_type = self._determine_edge_type(link_url)

                        edge = Edge(
                            id=self._generate_edge_id(),
                            source_id=source_id,
                            target_id=target_id,
                            edge_type=edge_type,
                            action=self._generate_action_label(link_url, edge_type),
                        )
                        graph.add_edge(edge)

            # Create edges for interactive elements if structure exists
            if page.structure:
                self._add_structure_edges(graph, page, source_id, url_to_node_id)

        # Also create edges from the site_map if available
        for source_url, links in crawl_result.site_map.items():
            source_id = url_to_node_id.get(source_url) or url_to_node_id.get(normalize_url(source_url))
            if not source_id:
                continue

            for link_url in links:
                if not is_same_domain(link_url, crawl_result.base_url):
                    continue

                normalized_link = normalize_url(link_url, crawl_result.base_url)
                target_id = url_to_node_id.get(normalized_link) or url_to_node_id.get(link_url)

                if target_id and target_id != source_id:
                    edge_key = (source_id, target_id)
                    if edge_key not in self._added_edges:
                        self._added_edges.add(edge_key)
                        edge = Edge(
                            id=self._generate_edge_id(),
                            source_id=source_id,
                            target_id=target_id,
                            edge_type=EdgeType.LINK,
                            action=self._generate_action_label(link_url, EdgeType.LINK),
                        )
                        graph.add_edge(edge)

        return graph

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from URL path."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            return parsed.netloc
        # Get the last segment and clean it
        segment = path.split('/')[-1]
        # Remove file extensions
        segment = segment.rsplit('.', 1)[0] if '.' in segment else segment
        # Convert dashes/underscores to spaces
        title = segment.replace('-', ' ').replace('_', ' ')
        return title.title() or url

    def _determine_edge_type(self, url: str) -> EdgeType:
        """Determine the type of edge based on URL patterns."""
        url_lower = url.lower()

        if any(x in url_lower for x in ['/nav', '/menu', 'navigation']):
            return EdgeType.NAVIGATION
        if any(x in url_lower for x in ['/form', '/submit', '/contact', '/signup', '/login', '/register']):
            return EdgeType.FORM_SUBMIT

        return EdgeType.LINK

    def _generate_action_label(self, url: str, edge_type: EdgeType) -> str:
        """Generate a human-readable action label."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        if not path:
            return "Go to homepage"

        # Get the last meaningful segment
        segments = [s for s in path.split('/') if s]
        if segments:
            segment = segments[-1].replace('-', ' ').replace('_', ' ').title()
            return f"Navigate to {segment}"

        return f"Navigate to {path}"

    def _extract_actions(self, page: PageData) -> list[dict[str, Any]]:
        """Extract available actions from a page."""
        actions = []

        if not page.structure:
            return actions

        # Buttons
        for btn in page.structure.buttons:
            actions.append({
                "type": "button_click",
                "element": btn.model_dump() if hasattr(btn, 'model_dump') else dict(btn),
                "description": f"Click button: {btn.text or btn.aria_label or 'unknown'}",
            })

        # Forms
        for form in page.structure.forms:
            actions.append({
                "type": "form_submit",
                "form": form.model_dump() if hasattr(form, 'model_dump') else dict(form),
                "description": f"Submit form to {form.action or 'same page'}",
                "required_fields": [f.name for f in form.fields if f.required],
            })

        # Links
        for link in page.structure.links:
            actions.append({
                "type": "navigation",
                "element": link.model_dump() if hasattr(link, 'model_dump') else dict(link),
                "description": f"Click link: {link.text or link.href or 'unknown'}",
            })

        # Dropdowns
        for dropdown in page.structure.dropdowns:
            actions.append({
                "type": "dropdown_select",
                "element": dropdown.model_dump() if hasattr(dropdown, 'model_dump') else dict(dropdown),
                "description": f"Select from dropdown: {dropdown.name or dropdown.id or 'unknown'}",
            })

        return actions

    def _determine_node_type(self, page: PageData) -> NodeType:
        """Determine the type of node based on page content."""
        url_lower = page.url.lower()
        title_lower = (page.title or "").lower()

        if any(x in url_lower for x in ["error", "404", "500", "not-found"]):
            return NodeType.ERROR_STATE
        if any(x in url_lower or x in title_lower for x in ["success", "thank", "confirm", "complete"]):
            return NodeType.SUCCESS_STATE
        if page.structure and page.structure.forms:
            return NodeType.FORM_STATE

        return NodeType.PAGE

    def _add_structure_edges(
        self,
        graph: FlowGraph,
        page: PageData,
        source_id: str,
        url_to_node_id: dict[str, str]
    ) -> None:
        """Add edges based on page structure elements."""
        if not page.structure:
            return

        # Navigation links
        for nav_link in page.structure.navigation_links:
            if nav_link.href:
                normalized_href = normalize_url(nav_link.href, page.url)
                target_id = url_to_node_id.get(normalized_href) or url_to_node_id.get(nav_link.href)

                if target_id and target_id != source_id:
                    edge_key = (source_id, target_id)
                    if edge_key not in self._added_edges:
                        self._added_edges.add(edge_key)
                        edge = Edge(
                            id=self._generate_edge_id(),
                            source_id=source_id,
                            target_id=target_id,
                            edge_type=EdgeType.NAVIGATION,
                            action=f"Click nav: {nav_link.text or nav_link.href}",
                            element=nav_link,
                        )
                        graph.add_edge(edge)

        # Forms - create edges to potential success/error states
        for form in page.structure.forms:
            if form.action:
                normalized_action = normalize_url(form.action, page.url)
                target_id = url_to_node_id.get(normalized_action) or url_to_node_id.get(form.action)

                if target_id:
                    edge_key = (source_id, target_id)
                    if edge_key not in self._added_edges:
                        self._added_edges.add(edge_key)
                        required_inputs = [
                            {"name": f.name, "type": f.input_type, "required": f.required}
                            for f in form.fields
                        ]
                        edge = Edge(
                            id=self._generate_edge_id(),
                            source_id=source_id,
                            target_id=target_id,
                            edge_type=EdgeType.FORM_SUBMIT,
                            action=f"Submit form ({form.method})",
                            required_inputs=required_inputs,
                        )
                        graph.add_edge(edge)
