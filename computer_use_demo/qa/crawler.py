"""
Web Crawler using Firecrawl for extracting DOM structure and interactive elements.
"""

import os
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse, urljoin
from firecrawl import Firecrawl
from firecrawl.types import ScrapeOptions
from pydantic import BaseModel, Field


def normalize_url(url: str, base_url: str | None = None) -> str:
    """Normalize URL for consistent comparison."""
    if not url:
        return ""
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip('/') or '/'
        return f"{parsed.scheme.lower()}://{netloc}{path}"
    except Exception:
        return url


def is_internal_link(link: str, base_url: str) -> bool:
    """Check if a link is internal to the base domain."""
    try:
        base_domain = urlparse(base_url).netloc.lower().replace('www.', '')
        link_domain = urlparse(link).netloc.lower().replace('www.', '')
        return link_domain == base_domain or not link_domain
    except Exception:
        return False


class InteractiveElement(BaseModel):
    """Represents an interactive element on a page."""
    element_type: str = Field(description="Type: button, link, input, form, select, etc.")
    selector: str = Field(description="CSS selector or XPath to locate the element")
    text: str | None = Field(default=None, description="Visible text content")
    href: str | None = Field(default=None, description="Link destination if applicable")
    input_type: str | None = Field(default=None, description="Input type if applicable (text, email, password, etc.)")
    name: str | None = Field(default=None, description="Name attribute")
    id: str | None = Field(default=None, description="ID attribute")
    placeholder: str | None = Field(default=None, description="Placeholder text")
    required: bool = Field(default=False, description="Whether the field is required")
    aria_label: str | None = Field(default=None, description="Accessibility label")


class FormData(BaseModel):
    """Represents a form on the page."""
    action: str | None = Field(default=None, description="Form action URL")
    method: str = Field(default="GET", description="Form method (GET/POST)")
    fields: list[InteractiveElement] = Field(default_factory=list, description="Form fields")
    submit_button: InteractiveElement | None = Field(default=None, description="Submit button")


class PageStructure(BaseModel):
    """Extracted structure of a webpage for QA purposes."""
    url: str = Field(description="Page URL")
    title: str = Field(description="Page title")
    description: str | None = Field(default=None, description="Meta description")
    navigation_links: list[InteractiveElement] = Field(default_factory=list, description="Navigation menu links")
    buttons: list[InteractiveElement] = Field(default_factory=list, description="All clickable buttons")
    links: list[InteractiveElement] = Field(default_factory=list, description="All links on the page")
    forms: list[FormData] = Field(default_factory=list, description="All forms on the page")
    inputs: list[InteractiveElement] = Field(default_factory=list, description="Standalone input fields")
    modals_triggers: list[InteractiveElement] = Field(default_factory=list, description="Elements that trigger modals/popups")
    dropdowns: list[InteractiveElement] = Field(default_factory=list, description="Dropdown/select elements")
    main_content_sections: list[str] = Field(default_factory=list, description="Main content section identifiers")


@dataclass
class PageData:
    """Data extracted from a single page."""
    url: str
    title: str
    markdown: str
    html: str | None
    links: list[str]
    structure: PageStructure | None
    metadata: dict[str, Any] = field(default_factory=dict)
    screenshot_base64: str | None = None


@dataclass
class CrawlResult:
    """Result of crawling a website."""
    base_url: str
    pages: list[PageData]
    total_pages: int
    site_map: dict[str, list[str]]  # URL -> list of linked URLs

    def get_all_urls(self) -> list[str]:
        return [page.url for page in self.pages]

    def get_page_by_url(self, url: str) -> PageData | None:
        for page in self.pages:
            if page.url == url:
                return page
        return None


class QACrawler:
    """
    Crawler for extracting website structure and interactive elements using Firecrawl.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY is required. Set it in .env or pass it directly.")
        self.client = Firecrawl(api_key=self.api_key)

    async def crawl_site(
        self,
        url: str,
        max_pages: int = 50,
        max_depth: int = 3,
        include_paths: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        extract_structure: bool = True,
    ) -> CrawlResult:
        """
        Crawl a website and extract structure for QA testing.

        Args:
            url: The base URL to start crawling from
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth to crawl (used in scrape options)
            include_paths: Glob patterns for paths to include
            exclude_paths: Glob patterns for paths to exclude
            extract_structure: Whether to extract detailed page structure using AI
        """
        # Build scrape options using modern SDK v2
        scrape_options = ScrapeOptions(formats=["markdown", "links"])

        # Execute crawl with v2 SDK syntax
        try:
            print(f"Starting crawl of {url} with limit={max_pages}")
            # Use the v2 crawl() method which waits for completion
            crawl_result = self.client.crawl(
                url,
                limit=max_pages,
                scrape_options=scrape_options,
                include_paths=include_paths,
                exclude_paths=exclude_paths,
                poll_interval=5,  # Poll every 5 seconds
            )
            print(f"Crawl completed. Result type: {type(crawl_result)}")
        except Exception as e:
            print(f"Crawl failed, falling back to single page scrape: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to single page scrape
            page_data = await self.scrape_single_page(url, extract_structure=extract_structure)
            return CrawlResult(
                base_url=url,
                pages=[page_data],
                total_pages=1,
                site_map={url: page_data.links},
            )

        # Process results - handle different response formats
        pages: list[PageData] = []
        site_map: dict[str, list[str]] = {}
        all_discovered_urls: set[str] = set()

        # The modern SDK returns a CrawlStatusResponse with a 'data' attribute
        # Debug log the result structure
        print(f"Crawl result attributes: {dir(crawl_result)}")
        if hasattr(crawl_result, 'data'):
            crawl_data = crawl_result.data if crawl_result.data else []
            print(f"Found {len(crawl_data)} pages in crawl_result.data")
        elif isinstance(crawl_result, dict):
            crawl_data = crawl_result.get('data', [])
            print(f"Found {len(crawl_data)} pages in dict data")
        elif isinstance(crawl_result, list):
            crawl_data = crawl_result
            print(f"Crawl result is a list with {len(crawl_data)} items")
        else:
            crawl_data = []
            print(f"Unknown crawl result format: {type(crawl_result)}")

        for page_data in crawl_data:
            # Handle both dict and object formats
            if isinstance(page_data, dict):
                metadata = page_data.get("metadata", {}) or {}
                page_url = metadata.get("sourceURL") or metadata.get("url") or metadata.get("ogUrl") or url
                page_links = page_data.get("links", []) or []
                page_markdown = page_data.get("markdown", "") or ""
                page_html = page_data.get("html")
                page_title = metadata.get("title", "")
            else:
                metadata = getattr(page_data, "metadata", {}) or {}
                if isinstance(metadata, dict):
                    page_url = metadata.get("sourceURL") or metadata.get("url") or metadata.get("ogUrl") or url
                    page_title = metadata.get("title", "")
                else:
                    page_url = getattr(metadata, "sourceURL", None) or getattr(metadata, "url", None) or url
                    page_title = getattr(metadata, "title", "")
                page_links = getattr(page_data, "links", []) or []
                page_markdown = getattr(page_data, "markdown", "") or ""
                page_html = getattr(page_data, "html", None)
                metadata = dict(metadata) if hasattr(metadata, '__iter__') else {}

            # Filter to internal links only and normalize
            internal_links = []
            for link in page_links:
                if isinstance(link, str) and is_internal_link(link, url):
                    normalized = normalize_url(link, url)
                    if normalized:
                        internal_links.append(normalized)
                        all_discovered_urls.add(normalized)

            # Normalize page URL
            normalized_page_url = normalize_url(page_url)
            site_map[normalized_page_url] = internal_links
            all_discovered_urls.add(normalized_page_url)

            page = PageData(
                url=normalized_page_url,
                title=page_title or self._extract_title_from_url(normalized_page_url),
                markdown=page_markdown,
                html=page_html,
                links=internal_links,
                structure=None,  # Skip AI extraction for speed
                metadata=dict(metadata) if metadata else {},
            )
            pages.append(page)

        # Build complete site map with all internal links
        final_site_map = {}
        for page_url, links in site_map.items():
            final_site_map[page_url] = [l for l in links if l in all_discovered_urls or any(
                normalize_url(p.url) == l for p in pages
            )]

        return CrawlResult(
            base_url=normalize_url(url),
            pages=pages,
            total_pages=len(pages),
            site_map=final_site_map,
        )

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from URL path."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            return parsed.netloc
        segment = path.split('/')[-1]
        segment = segment.rsplit('.', 1)[0] if '.' in segment else segment
        title = segment.replace('-', ' ').replace('_', ' ')
        return title.title() or url

    async def scrape_single_page(
        self,
        url: str,
        extract_structure: bool = True,
        take_screenshot: bool = False,
    ) -> PageData:
        """
        Scrape a single page for detailed analysis.
        """
        formats = ["markdown", "links"]
        if take_screenshot:
            formats.append("screenshot")

        try:
            # Use v2 SDK scrape() method
            result = self.client.scrape(url, formats=formats)
            print(f"Scraped {url}, result type: {type(result)}")
        except Exception as e:
            print(f"Warning: Scrape failed for {url}: {e}")
            import traceback
            traceback.print_exc()
            return PageData(
                url=url,
                title="",
                markdown="",
                html=None,
                links=[],
                structure=None,
                metadata={},
            )

        # Handle both dict and object response formats
        if isinstance(result, dict):
            metadata = result.get("metadata", {}) or {}
            markdown = result.get("markdown", "") or ""
            html = result.get("html")
            links = result.get("links", []) or []
            screenshot = result.get("screenshot")
            title = metadata.get("title", "") if metadata else ""
        else:
            metadata = getattr(result, "metadata", {}) or {}
            markdown = getattr(result, "markdown", "") or ""
            html = getattr(result, "html", None)
            links = getattr(result, "links", []) or []
            screenshot = getattr(result, "screenshot", None)
            if isinstance(metadata, dict):
                title = metadata.get("title", "")
            else:
                title = getattr(metadata, "title", "")
            metadata = dict(metadata) if hasattr(metadata, '__iter__') and isinstance(metadata, dict) else {}

        return PageData(
            url=url,
            title=title,
            markdown=markdown,
            html=html,
            links=links,
            structure=None,  # Skip AI extraction for speed
            metadata=metadata,
            screenshot_base64=screenshot,
        )

    async def _extract_page_structure(self, url: str) -> PageStructure | None:
        """
        Use Firecrawl's AI extraction to get detailed page structure.
        Note: This is an advanced feature that may not be available on all plans.
        """
        try:
            # Use v2 scrape with extract format
            result = self.client.scrape(
                url,
                formats=["extract"],
                extract={
                    "schema": PageStructure.model_json_schema(),
                    "prompt": """Extract all interactive elements from this webpage for QA testing purposes.

Focus on:
1. Navigation links (menus, nav bars)
2. All buttons (submit, action buttons, toggles)
3. All forms with their fields (inputs, selects, textareas)
4. Links that navigate to other pages
5. Elements that trigger modals or popups
6. Dropdown menus and select elements
7. Input fields outside of forms

For each element, try to identify:
- A reliable CSS selector or XPath
- The element type
- Any text content or labels
- Validation requirements (required, type constraints)
- Accessibility labels (aria-label, title)

Be thorough - we need this for automated testing."""
                }
            )

            # Handle response format
            if isinstance(result, dict):
                extracted = result.get("extract")
            else:
                extracted = getattr(result, "extract", None)

            if extracted:
                return PageStructure(**extracted)
        except Exception as e:
            print(f"Warning: Could not extract structure for {url}: {e}")

        return None

    def map_site(self, url: str, limit: int = 500) -> list[str]:
        """
        Quickly map all URLs on a site without full scraping.
        """
        try:
            # Use v2 map() method
            result = self.client.map(url, limit=limit)
            # Handle different response formats
            if isinstance(result, dict):
                links = result.get("links", [])
            elif hasattr(result, "links"):
                links = result.links or []
            else:
                links = result if isinstance(result, list) else []

            # Extract URLs from links
            urls = []
            for link in links:
                if isinstance(link, str):
                    urls.append(link)
                elif hasattr(link, 'url'):
                    urls.append(link.url)
                elif isinstance(link, dict) and 'url' in link:
                    urls.append(link['url'])
            return urls
        except Exception as e:
            print(f"Warning: Could not map site {url}: {e}")
            return []
