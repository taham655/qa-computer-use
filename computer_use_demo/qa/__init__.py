"""
AI-Automated QA System
- Crawls websites using Firecrawl
- Generates flow graphs from DOM structure
- Uses AI to generate test cases
"""

from .crawler import QACrawler, CrawlResult, PageData
from .flow_graph import FlowGraph, FlowGraphGenerator, Node, Edge
from .test_generator import TestGenerator, TestCase, TestType, TestPriority
from .test_executor import TestExecutor, TestResult, TestSuiteResult, TestReporter

__all__ = [
    "QACrawler",
    "CrawlResult",
    "PageData",
    "FlowGraph",
    "FlowGraphGenerator",
    "Node",
    "Edge",
    "TestGenerator",
    "TestCase",
    "TestType",
    "TestPriority",
    "TestExecutor",
    "TestResult",
    "TestSuiteResult",
    "TestReporter",
]
