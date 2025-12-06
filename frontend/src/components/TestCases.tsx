import { useState } from 'react';
import { FlaskConical, ChevronDown, ChevronRight, Download, Play, Code } from 'lucide-react';
import type { TestCase } from '@/types';
import clsx from 'clsx';

interface TestCasesProps {
  tests: TestCase[];
  onExecute: () => void;
  onExport: (format: 'json' | 'playwright') => void;
  loading: boolean;
}

const PRIORITY_CONFIG: Record<string, { color: string; bg: string; border: string }> = {
  critical: { color: 'text-accent-red', bg: 'bg-accent-red/15', border: 'border-accent-red/30' },
  high: { color: 'text-orange-400', bg: 'bg-orange-400/15', border: 'border-orange-400/30' },
  medium: { color: 'text-accent-yellow', bg: 'bg-accent-yellow/15', border: 'border-accent-yellow/30' },
  low: { color: 'text-accent-green', bg: 'bg-accent-green/15', border: 'border-accent-green/30' },
};

export function TestCases({ tests, onExecute, onExport, loading }: TestCasesProps) {
  const [priorityFilter, setPriorityFilter] = useState<string[]>(['critical', 'high', 'medium', 'low']);
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set());

  const filteredTests = tests.filter((t) => priorityFilter.includes(t.priority));

  const toggleTest = (id: string) => {
    setExpandedTests((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const togglePriority = (priority: string) => {
    setPriorityFilter((prev) =>
      prev.includes(priority)
        ? prev.filter((p) => p !== priority)
        : [...prev, priority]
    );
  };

  return (
    <section className="mb-8 animate-slide-up" style={{ animationDelay: '300ms' }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-accent-purple/15">
            <FlaskConical className="w-4 h-4 text-accent-purple" />
          </div>
          <h2 className="text-base font-semibold text-text-primary">
            Generated Test Cases
          </h2>
          <span className="text-text-tertiary text-xs bg-bg-hover px-2 py-0.5 rounded-full">
            {tests.length} tests
          </span>
        </div>
      </div>

      {/* Priority Filter */}
      <div className="flex items-center gap-2 mb-5">
        <span className="text-xs text-text-secondary">Filter:</span>
        {['critical', 'high', 'medium', 'low'].map((priority) => {
          const config = PRIORITY_CONFIG[priority];
          return (
            <button
              key={priority}
              onClick={() => togglePriority(priority)}
              className={clsx(
                'px-2.5 py-1 rounded-lg text-xs font-medium transition-all border capitalize',
                priorityFilter.includes(priority)
                  ? `${config.bg} ${config.color} ${config.border}`
                  : 'bg-bg-hover text-text-tertiary border-transparent opacity-60'
              )}
            >
              {priority}
            </button>
          );
        })}
      </div>

      {/* Test Cards */}
      <div className="space-y-2 mb-5">
        {filteredTests.map((test) => (
          <TestCard
            key={test.id}
            test={test}
            expanded={expandedTests.has(test.id)}
            onToggle={() => toggleTest(test.id)}
          />
        ))}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-4 border-t border-border">
        <button
          onClick={onExecute}
          disabled={loading}
          className={clsx(
            'flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all text-sm',
            loading
              ? 'bg-bg-tertiary text-text-tertiary cursor-not-allowed border border-border'
              : 'bg-accent-primary text-bg-primary hover:bg-accent-secondary shadow-soft'
          )}
        >
          <Play className="w-4 h-4" />
          Execute Tests
        </button>

        <button
          onClick={() => onExport('playwright')}
          className="flex items-center gap-2 px-4 py-2.5 bg-bg-tertiary border border-border rounded-xl hover:border-accent-primary hover:text-accent-primary transition-colors text-sm text-text-secondary"
        >
          <Download className="w-4 h-4" />
          Playwright
        </button>

        <button
          onClick={() => onExport('json')}
          className="flex items-center gap-2 px-4 py-2.5 bg-bg-tertiary border border-border rounded-xl hover:border-accent-primary hover:text-accent-primary transition-colors text-sm text-text-secondary"
        >
          <Code className="w-4 h-4" />
          JSON
        </button>
      </div>
    </section>
  );
}

function TestCard({
  test,
  expanded,
  onToggle,
}: {
  test: TestCase;
  expanded: boolean;
  onToggle: () => void;
}) {
  const priorityConfig = PRIORITY_CONFIG[test.priority];

  return (
    <div className="bg-bg-tertiary border border-border rounded-xl overflow-hidden hover:border-accent-primary/30 hover:shadow-soft transition-all">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 text-left"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-accent-primary text-xs bg-accent-light px-1.5 py-0.5 rounded">
              {test.id}
            </span>
            <span className="font-medium text-sm text-text-primary truncate">{test.name}</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2 py-0.5 bg-bg-hover text-text-secondary rounded capitalize">
              {test.type.replace('_', ' ')}
            </span>
            <span className={clsx('px-2 py-0.5 rounded capitalize border', priorityConfig.bg, priorityConfig.color, priorityConfig.border)}>
              {test.priority}
            </span>
          </div>
        </div>
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-text-tertiary flex-shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 text-text-tertiary flex-shrink-0" />
        )}
      </button>

      {expanded && (
        <div className="border-t border-border p-4 bg-bg-hover/50">
          <p className="text-text-secondary text-sm mb-4">{test.description}</p>

          {test.preconditions.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-medium text-text-primary mb-2 uppercase tracking-wide">Preconditions</h4>
              <ul className="list-disc list-inside text-xs text-text-secondary space-y-0.5">
                {test.preconditions.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mb-4">
            <h4 className="text-xs font-medium text-text-primary mb-2 uppercase tracking-wide">Steps</h4>
            <div className="space-y-2">
              {test.steps.map((step) => (
                <div key={step.order} className="flex items-start gap-2 text-xs">
                  <span className="font-mono text-accent-primary bg-accent-light px-1.5 py-0.5 rounded min-w-[24px] text-center">
                    {step.order}
                  </span>
                  <div className="flex-1">
                    <code className="text-accent-purple font-medium">{step.action}</code>
                    <span className="text-text-tertiary"> → </span>
                    <code className="text-text-secondary">{step.target}</code>
                    {step.value && (
                      <span className="text-text-secondary"> with <code className="text-accent-yellow">{step.value}</code></span>
                    )}
                    {step.expected_result && (
                      <p className="text-text-tertiary mt-0.5">
                        Expected: {step.expected_result}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {Object.keys(test.test_data).length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-text-primary mb-2 uppercase tracking-wide">Test Data</h4>
              <pre className="text-xs bg-bg-primary border border-border p-3 rounded-lg overflow-x-auto text-text-secondary">
                {JSON.stringify(test.test_data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
