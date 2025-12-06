import { useState, useEffect, useCallback } from 'react';
import { Header } from '@/components/Header';
import { NavSidebar, type NavPage } from '@/components/NavSidebar';
import { ConfigPanel } from '@/components/ConfigPanel';
import { PastTests } from '@/components/PastTests';
import { UrlInput } from '@/components/UrlInput';
import { CrawlResults } from '@/components/CrawlResults';
import { FlowGraph } from '@/components/FlowGraph';
import { TestCases } from '@/components/TestCases';
import { ExecutionView } from '@/components/ExecutionView';
import { GenerateTestsButton } from '@/components/GenerateTestsButton';
import { useApi } from '@/hooks/useApi';
import { useWebSocket } from '@/hooks/useWebSocket';
import { api } from '@/lib/api';
import type {
  APIKeyStatus,
  CrawlResponse,
  TestGenerationResponse,
  ViewMode,
  TestCase,
  SavedSession,
} from '@/types';

interface Settings {
  maxPages: number;
  maxDepth: number;
  extractStructure: boolean;
  testTypes: string[];
  maxTests: number;
  aiProvider: string;
}

const DEFAULT_SETTINGS: Settings = {
  maxPages: 25,
  maxDepth: 3,
  extractStructure: false,
  testTypes: ['happy_path', 'edge_case', 'error_handling'],
  maxTests: 15,
  aiProvider: 'openai',
};

export default function App() {
  // Navigation state
  const [activePage, setActivePage] = useState<NavPage>(() => {
    const saved = localStorage.getItem('qa_active_page');
    return (saved as NavPage) || 'home';
  });

  // State - restore from localStorage if available
  const [settings, setSettings] = useState<Settings>(() => {
    const saved = localStorage.getItem('qa_settings');
    return saved ? JSON.parse(saved) : DEFAULT_SETTINGS;
  });
  const [keyStatus, setKeyStatus] = useState<APIKeyStatus | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('setup');
  const [sessionId, setSessionId] = useState<string | null>(() => {
    return localStorage.getItem('qa_session_id');
  });
  const [crawlData, setCrawlData] = useState<CrawlResponse | null>(() => {
    const saved = localStorage.getItem('qa_crawl_data');
    return saved ? JSON.parse(saved) : null;
  });
  const [mermaidCode, setMermaidCode] = useState<string>('');
  const [testData, setTestData] = useState<TestGenerationResponse | null>(() => {
    const saved = localStorage.getItem('qa_test_data');
    return saved ? JSON.parse(saved) : null;
  });
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'running' | 'complete' | 'error'>('idle');

  // Past sessions
  const [savedSessions, setSavedSessions] = useState<SavedSession[]>(() => {
    const saved = localStorage.getItem('qa_saved_sessions');
    return saved ? JSON.parse(saved) : [];
  });

  // Persist navigation state
  useEffect(() => {
    localStorage.setItem('qa_active_page', activePage);
  }, [activePage]);

  // Persist state to localStorage
  useEffect(() => {
    if (sessionId) localStorage.setItem('qa_session_id', sessionId);
    else localStorage.removeItem('qa_session_id');
  }, [sessionId]);

  useEffect(() => {
    if (crawlData) localStorage.setItem('qa_crawl_data', JSON.stringify(crawlData));
    else localStorage.removeItem('qa_crawl_data');
  }, [crawlData]);

  useEffect(() => {
    if (testData) localStorage.setItem('qa_test_data', JSON.stringify(testData));
    else localStorage.removeItem('qa_test_data');
  }, [testData]);

  useEffect(() => {
    localStorage.setItem('qa_settings', JSON.stringify(settings));
  }, [settings]);

  useEffect(() => {
    localStorage.setItem('qa_saved_sessions', JSON.stringify(savedSessions));
  }, [savedSessions]);

  // API hooks
  const crawlApi = useApi(api.crawl);
  const testGenApi = useApi(api.generateTests);

  // Track the last summary message
  const [lastSummary, setLastSummary] = useState<string | undefined>();

  // WebSocket for execution
  const ws = useWebSocket({
    onMessage: (msg) => {
      // Capture summary from assistant messages (the last message content is usually the summary)
      if (msg.type === 'message' && msg.role === 'assistant' && msg.content) {
        setLastSummary(msg.content);
      }

      if (msg.type === 'status') {
        if (msg.status === 'complete') {
          setExecutionStatus('complete');
          // Save session on completion with the last summary
          if (sessionId && crawlData) {
            saveCurrentSession('completed', lastSummary);
          }
        } else if (msg.status === 'error') {
          setExecutionStatus('error');
          if (sessionId && crawlData) {
            saveCurrentSession('failed', lastSummary);
          }
        }
      } else if (msg.type === 'error') {
        setExecutionStatus('error');
      }
    },
  });

  // Fetch API key status on mount
  useEffect(() => {
    api.getKeyStatus().then(setKeyStatus).catch(console.error);
  }, []);

  // Save current session to history
  const saveCurrentSession = useCallback((status: 'completed' | 'failed' | 'pending', summary?: string) => {
    if (!sessionId || !crawlData) return;

    const existingIndex = savedSessions.findIndex(s => s.id === sessionId);
    const session: SavedSession = {
      id: sessionId,
      url: crawlData.crawl_result.base_url,
      createdAt: new Date().toISOString(),
      testCount: testData?.test_count || 0,
      status,
      pagesFound: crawlData.stats.pages_found,
      summary,
    };

    if (existingIndex >= 0) {
      const updated = [...savedSessions];
      updated[existingIndex] = session;
      setSavedSessions(updated);
    } else {
      setSavedSessions([session, ...savedSessions]);
    }
  }, [sessionId, crawlData, testData, savedSessions]);

  // Handle settings change
  const handleSettingsChange = useCallback((key: string, value: unknown) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  }, []);

  // Handle reset
  const handleReset = useCallback(() => {
    // Clear localStorage
    localStorage.removeItem('qa_session_id');
    localStorage.removeItem('qa_crawl_data');
    localStorage.removeItem('qa_test_data');
    localStorage.removeItem('qa_settings');

    setSettings(DEFAULT_SETTINGS);
    setViewMode('setup');
    setSessionId(null);
    setCrawlData(null);
    setMermaidCode('');
    setTestData(null);
    setExecutionStatus('idle');
    crawlApi.reset();
    testGenApi.reset();
    ws.clearMessages();
  }, [crawlApi, testGenApi, ws]);

  // Handle crawl
  const handleCrawl = useCallback(async (url: string) => {
    try {
      const result = await crawlApi.execute(url, {
        max_pages: settings.maxPages,
        max_depth: settings.maxDepth,
        extract_structure: settings.extractStructure,
      });

      setSessionId(result.session_id);
      setCrawlData(result);

      // Fetch mermaid diagram
      try {
        const mermaid = await api.getFlowGraphMermaid(result.session_id);
        setMermaidCode(mermaid.mermaid);
      } catch {
        console.error('Failed to fetch mermaid diagram');
      }
    } catch (error) {
      console.error('Crawl failed:', error);
    }
  }, [crawlApi, settings]);

  // Handle test generation
  const handleGenerateTests = useCallback(async () => {
    if (!sessionId) return;

    try {
      const result = await testGenApi.execute(sessionId, {
        test_types: settings.testTypes,
        max_tests: settings.maxTests,
        ai_provider: settings.aiProvider,
      });

      setTestData(result);
    } catch (error) {
      console.error('Test generation failed:', error);
    }
  }, [sessionId, testGenApi, settings]);

  // Handle test execution
  const handleExecuteTests = useCallback(async () => {
    if (!sessionId) {
      console.error('No session ID');
      return;
    }

    // Verify session has tests before connecting
    try {
      const sessionState = await api.getSession(sessionId);
      if (sessionState.test_count === 0) {
        console.error('No tests in session');
        setExecutionStatus('error');
        return;
      }
    } catch (error) {
      console.error('Session not found:', error);
      setExecutionStatus('error');
      return;
    }

    setViewMode('execution');
    setExecutionStatus('running');
    ws.clearMessages();
    ws.connect(sessionId);
  }, [sessionId, ws]);

  // Handle export
  const handleExport = useCallback(async (format: 'json' | 'playwright') => {
    if (!sessionId) return;

    try {
      const result = await api.exportTests(sessionId, format);

      // Create download
      const blob = new Blob([result.content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  }, [sessionId]);

  // Handle load session from history
  const handleLoadSession = useCallback(async (id: string) => {
    try {
      const session = await api.getSession(id);
      setSessionId(id);
      // Navigate to run-test page
      setActivePage('run-test');
      // Note: We'd need to reload crawl data and test data here
      // For now, just set the session ID
    } catch (error) {
      console.error('Failed to load session:', error);
      // Remove from saved sessions if not found
      setSavedSessions(prev => prev.filter(s => s.id !== id));
    }
  }, []);

  // Handle delete session
  const handleDeleteSession = useCallback((id: string) => {
    setSavedSessions(prev => prev.filter(s => s.id !== id));
    // Also delete from backend
    api.deleteSession(id).catch(console.error);
  }, []);

  // Handle new test button
  const handleNewTest = useCallback(() => {
    handleReset();
    setActivePage('run-test');
  }, [handleReset]);

  // Handle back to setup from execution
  const handleBackToSetup = useCallback(() => {
    setViewMode('setup');
  }, []);

  // Handle back to home from execution
  const handleBackToHome = useCallback(() => {
    setViewMode('setup');
    setActivePage('home');
  }, []);

  // Check if we're in execution mode
  const isExecutionMode = viewMode === 'execution';

  return (
    <div className="flex min-h-screen bg-bg-secondary">
      {/* Left Navigation Sidebar - Hidden during execution */}
      {!isExecutionMode && (
        <NavSidebar activePage={activePage} onNavigate={setActivePage} />
      )}

      {/* Main Content */}
      <main className={`flex-1 ${isExecutionMode ? 'p-0' : 'p-6'} overflow-y-auto`}>
        {activePage === 'home' ? (
          <PastTests
            sessions={savedSessions}
            onLoadSession={handleLoadSession}
            onDeleteSession={handleDeleteSession}
            onNewTest={handleNewTest}
          />
        ) : (
          <>
            {viewMode === 'setup' && <Header />}

            {viewMode === 'setup' ? (
              <>
                <UrlInput onCrawl={handleCrawl} loading={crawlApi.loading} />

                {crawlApi.error && (
                  <div className="mb-6 p-4 bg-accent-red/15 border border-accent-red/30 rounded-xl text-accent-red text-sm">
                    {crawlApi.error}
                  </div>
                )}

                {crawlData && (
                  <>
                    <CrawlResults stats={crawlData.stats} pages={crawlData.crawl_result.pages} />
                    <FlowGraph flowGraph={crawlData.flow_graph} mermaidCode={mermaidCode} />

                    {!testData && (
                      <GenerateTestsButton
                        onClick={handleGenerateTests}
                        loading={testGenApi.loading}
                        disabled={!sessionId}
                      />
                    )}

                    {testGenApi.error && (
                      <div className="mb-6 p-4 bg-accent-red/15 border border-accent-red/30 rounded-xl text-accent-red text-sm">
                        {testGenApi.error}
                      </div>
                    )}

                    {testData && (
                      <TestCases
                        tests={testData.tests as TestCase[]}
                        onExecute={handleExecuteTests}
                        onExport={handleExport}
                        loading={false}
                      />
                    )}
                  </>
                )}
              </>
            ) : (
              <ExecutionView
                messages={ws.messages}
                tests={testData?.tests as TestCase[] ?? []}
                targetUrl={crawlData?.crawl_result.base_url ?? ''}
                status={executionStatus}
                flowGraph={crawlData?.flow_graph}
                pages={crawlData?.crawl_result.pages}
                onBackToHome={handleBackToHome}
              />
            )}
          </>
        )}
      </main>

      {/* Right Configuration Panel - Only on Run Test page in setup mode */}
      {activePage === 'run-test' && viewMode === 'setup' && (
        <ConfigPanel
          settings={settings}
          onSettingsChange={handleSettingsChange}
          onReset={handleReset}
        />
      )}
    </div>
  );
}
