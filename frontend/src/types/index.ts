export interface APIKeyStatus {
  firecrawl: boolean;
  openai: boolean;
  anthropic: boolean;
}

export interface CrawlStats {
  pages_found: number;
  total_links: number;
  forms_found: number;
  interactive_elements: number;
  nodes: number;
  edges: number;
  critical_paths: number;
}

export interface PageData {
  url: string;
  title: string;
  link_count: number;
  has_structure: boolean;
  forms_count: number;
  buttons_count: number;
  inputs_count: number;
  links_count: number;
}

export interface CrawlResult {
  base_url: string;
  total_pages: number;
  pages: PageData[];
  site_map: Record<string, string[]>;
}

export interface FlowGraphNode {
  id: string;
  url: string;
  title: string;
  type: string;
  actions: unknown[];
  metadata: Record<string, unknown>;
}

export interface FlowGraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  action: string;
  required_inputs: unknown[];
  preconditions: string[];
}

export interface FlowGraph {
  base_url: string;
  nodes: Record<string, FlowGraphNode>;
  edges: FlowGraphEdge[];
  entry_points: string[];
  stats: {
    total_nodes: number;
    total_edges: number;
    total_paths: number;
  };
}

export interface TestStep {
  order: number;
  action: string;
  target: string;
  value?: string;
  expected_result?: string;
  screenshot?: boolean;
}

export interface TestCase {
  id: string;
  name: string;
  description: string;
  type: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  steps: TestStep[];
  preconditions: string[];
  test_data: Record<string, unknown>;
  tags: string[];
  estimated_duration: number;
}

export interface CrawlResponse {
  session_id: string;
  crawl_result: CrawlResult;
  flow_graph: FlowGraph;
  stats: CrawlStats;
}

export interface TestGenerationResponse {
  test_count: number;
  tests: TestCase[];
  playwright_code: string;
}

export interface SessionState {
  id: string;
  target_url: string | null;
  has_crawl_result: boolean;
  has_flow_graph: boolean;
  test_count: number;
  execution_status: string;
  created_at: string;
}

export type ViewMode = 'setup' | 'execution';
export type NavPage = 'home' | 'run-test';

export interface SavedSession {
  id: string;
  url: string;
  createdAt: string;
  testCount: number;
  status: 'completed' | 'failed' | 'pending';
  pagesFound: number;
  summary?: string;
}

export interface ExecutionMessage {
  type: 'status' | 'message' | 'tool_use' | 'tool_result' | 'error';
  role?: string;
  content?: string;
  status?: string;
  message?: string;
  name?: string;
  input?: Record<string, unknown>;
  tool_id?: string;
  output?: string;
  error?: string;
  screenshot?: string;
}
