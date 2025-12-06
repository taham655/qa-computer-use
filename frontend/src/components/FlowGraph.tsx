import { useState, useEffect, useRef } from 'react';
import { GitBranch, ChevronDown, ChevronRight, Code, Share2 } from 'lucide-react';
import { StatsCard } from './StatsCard';
import type { FlowGraph as FlowGraphType } from '@/types';
import mermaid from 'mermaid';

interface FlowGraphProps {
  flowGraph: FlowGraphType;
  mermaidCode: string;
}

// Initialize mermaid with dark theme
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#1f1f1f',
    primaryTextColor: '#f5f5f5',
    primaryBorderColor: '#60a5fa',
    lineColor: '#6b6b6b',
    secondaryColor: '#1a1a1a',
    tertiaryColor: '#141414',
    fontFamily: 'DM Sans, system-ui, sans-serif',
    background: '#0d0d0d',
    mainBkg: '#1f1f1f',
    nodeBorder: '#3a3a3a',
    clusterBkg: '#1a1a1a',
    titleColor: '#f5f5f5',
    edgeLabelBackground: '#1f1f1f',
  },
});

export function FlowGraph({ flowGraph, mermaidCode }: FlowGraphProps) {
  const [diagramExpanded, setDiagramExpanded] = useState(true);
  const [jsonExpanded, setJsonExpanded] = useState(false);
  const mermaidRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (diagramExpanded && mermaidRef.current && mermaidCode) {
      const renderDiagram = async () => {
        try {
          mermaidRef.current!.innerHTML = '';
          const { svg } = await mermaid.render('flow-diagram', mermaidCode);
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = svg;
          }
        } catch {
          // If mermaid fails, show the code instead
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = `<pre class="text-text-secondary text-sm">${mermaidCode}</pre>`;
          }
        }
      };
      renderDiagram();
    }
  }, [diagramExpanded, mermaidCode]);

  const nodeCount = Object.keys(flowGraph.nodes).length;
  const edgeCount = flowGraph.edges.length;
  const criticalPaths = flowGraph.stats?.total_paths || 0;

  return (
    <section className="mb-8 animate-slide-up" style={{ animationDelay: '200ms' }}>
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 rounded-lg bg-accent-cyan/15">
          <Share2 className="w-4 h-4 text-accent-cyan" />
        </div>
        <h2 className="text-base font-semibold text-text-primary">
          Flow Graph
        </h2>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        <StatsCard value={nodeCount} label="Nodes" delay={0} />
        <StatsCard value={edgeCount} label="Edges" delay={100} />
        <StatsCard value={criticalPaths} label="Critical Paths" delay={200} />
      </div>

      {/* Mermaid Diagram */}
      <div className="bg-bg-tertiary border border-border rounded-xl overflow-hidden mb-3 shadow-soft">
        <button
          onClick={() => setDiagramExpanded(!diagramExpanded)}
          className="w-full flex items-center justify-between p-4 hover:bg-bg-hover transition-colors"
        >
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-accent-primary" />
            <span className="font-medium text-sm text-text-primary">Visual Graph</span>
            <span className="text-xs text-text-tertiary">(Mermaid)</span>
          </div>
          {diagramExpanded ? (
            <ChevronDown className="w-4 h-4 text-text-tertiary" />
          ) : (
            <ChevronRight className="w-4 h-4 text-text-tertiary" />
          )}
        </button>

        {diagramExpanded && (
          <div className="border-t border-border p-5 overflow-x-auto bg-bg-primary/50">
            <div ref={mermaidRef} className="min-h-[180px] flex items-center justify-center" />
          </div>
        )}
      </div>

      {/* JSON Export */}
      <div className="bg-bg-tertiary border border-border rounded-xl overflow-hidden shadow-soft">
        <button
          onClick={() => setJsonExpanded(!jsonExpanded)}
          className="w-full flex items-center justify-between p-4 hover:bg-bg-hover transition-colors"
        >
          <div className="flex items-center gap-2">
            <Code className="w-4 h-4 text-accent-primary" />
            <span className="font-medium text-sm text-text-primary">Graph JSON</span>
          </div>
          {jsonExpanded ? (
            <ChevronDown className="w-4 h-4 text-text-tertiary" />
          ) : (
            <ChevronRight className="w-4 h-4 text-text-tertiary" />
          )}
        </button>

        {jsonExpanded && (
          <div className="border-t border-border bg-bg-primary/50">
            <pre className="p-4 text-xs text-text-secondary overflow-x-auto max-h-80 font-mono">
              {JSON.stringify(flowGraph, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </section>
  );
}
