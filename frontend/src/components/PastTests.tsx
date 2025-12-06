import { useState } from 'react';
import { Clock, Globe, CheckCircle2, XCircle, Play, Trash2, FileText, Plus, History, ChevronDown, ChevronRight, ScrollText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';

interface TestSession {
  id: string;
  url: string;
  createdAt: string;
  testCount: number;
  status: 'completed' | 'failed' | 'pending';
  pagesFound: number;
  summary?: string;
}

interface PastTestsProps {
  sessions: TestSession[];
  onLoadSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onNewTest: () => void;
}

export function PastTests({ sessions, onLoadSession, onDeleteSession, onNewTest }: PastTestsProps) {
  return (
    <div className="max-w-4xl mx-auto py-4">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-xl bg-accent-light">
            <History className="w-6 h-6 text-accent-primary" />
          </div>
          <h1 className="text-2xl font-bold text-text-primary">
            Test History
          </h1>
        </div>
        <p className="text-text-secondary text-sm ml-14">
          View and manage your past test sessions
        </p>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3 mb-8">
        <button
          onClick={onNewTest}
          className="flex items-center gap-2 px-5 py-2.5 bg-accent-primary text-bg-primary rounded-xl font-medium hover:bg-accent-secondary transition-colors shadow-soft"
        >
          <Plus className="w-4 h-4" />
          New Test Run
        </button>
      </div>

      {/* Sessions List */}
      {sessions.length === 0 ? (
        <EmptyState onNewTest={onNewTest} />
      ) : (
        <div className="space-y-3">
          {sessions.map((session, index) => (
            <SessionCard
              key={session.id}
              session={session}
              index={index}
              onLoad={() => onLoadSession(session.id)}
              onDelete={() => onDeleteSession(session.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function EmptyState({ onNewTest }: { onNewTest: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 bg-bg-tertiary border border-border rounded-2xl shadow-soft">
      <div className="w-16 h-16 rounded-2xl bg-accent-light flex items-center justify-center mb-5">
        <FileText className="w-8 h-8 text-accent-primary" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary mb-1.5">No Test Sessions Yet</h3>
      <p className="text-text-secondary text-sm text-center max-w-md mb-6">
        Start by running your first test. Crawl a website, generate test cases, and execute them to see results here.
      </p>
      <button
        onClick={onNewTest}
        className="flex items-center gap-2 px-5 py-2.5 bg-accent-primary text-bg-primary rounded-xl font-medium hover:bg-accent-secondary transition-colors shadow-soft"
      >
        <Play className="w-4 h-4" />
        Start First Test
      </button>
    </div>
  );
}

interface SessionCardProps {
  session: TestSession;
  index: number;
  onLoad: () => void;
  onDelete: () => void;
}

function SessionCard({ session, index, onLoad, onDelete }: SessionCardProps) {
  const [summaryExpanded, setSummaryExpanded] = useState(false);
  const hasSummary = !!session.summary;

  const statusConfig = {
    completed: { icon: CheckCircle2, color: 'text-accent-green', bg: 'bg-accent-green/15', borderColor: 'border-accent-green/30', label: 'Completed' },
    failed: { icon: XCircle, color: 'text-accent-red', bg: 'bg-accent-red/15', borderColor: 'border-accent-red/30', label: 'Failed' },
    pending: { icon: Clock, color: 'text-accent-yellow', bg: 'bg-accent-yellow/15', borderColor: 'border-accent-yellow/30', label: 'Pending' },
  };

  const config = statusConfig[session.status];
  const StatusIcon = config.icon;

  return (
    <div
      className="group bg-bg-tertiary border border-border rounded-xl hover:border-accent-primary/30 hover:shadow-card transition-all duration-200 animate-fade-in overflow-hidden"
      style={{ animationDelay: `${index * 40}ms` }}
    >
      <div className="p-4 flex items-center justify-between">
        {/* Left Section */}
        <div className="flex items-center gap-4 flex-1 min-w-0">
          {/* Status Icon */}
          <div className={clsx('p-2.5 rounded-xl', config.bg, config.borderColor, 'border')}>
            <StatusIcon className={clsx('w-5 h-5', config.color)} />
          </div>

          {/* Info */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Globe className="w-4 h-4 text-text-tertiary flex-shrink-0" />
              <span className="font-medium text-text-primary truncate text-sm">{session.url}</span>
            </div>
            <div className="flex items-center gap-4 text-xs text-text-secondary">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatDate(session.createdAt)}
              </span>
              <span className="text-text-tertiary">•</span>
              <span>{session.pagesFound} pages</span>
              <span className="text-text-tertiary">•</span>
              <span>{session.testCount} tests</span>
            </div>
          </div>
        </div>

        {/* Right Section - Actions */}
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          {hasSummary && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSummaryExpanded(!summaryExpanded);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-accent-purple/15 text-accent-purple rounded-lg hover:bg-accent-purple hover:text-bg-primary transition-colors text-sm font-medium"
            >
              <ScrollText className="w-3.5 h-3.5" />
              Summary
              {summaryExpanded ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronRight className="w-3 h-3" />
              )}
            </button>
          )}
          <button
            onClick={onLoad}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-accent-light text-accent-primary rounded-lg hover:bg-accent-primary hover:text-bg-primary transition-colors text-sm font-medium"
          >
            <Play className="w-3.5 h-3.5" />
            Load
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="p-1.5 text-text-tertiary hover:text-accent-red hover:bg-accent-red/15 rounded-lg transition-colors"
            title="Delete session"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        {/* Status Badge */}
        <div className={clsx(
          'ml-4 px-2.5 py-1 rounded-full text-xs font-medium border',
          config.bg, config.color, config.borderColor
        )}>
          {config.label}
        </div>
      </div>

      {/* Expandable Summary Section */}
      {hasSummary && summaryExpanded && (
        <div className="border-t border-border bg-bg-hover/50 p-4">
          <div className="flex items-center gap-2 mb-3">
            <ScrollText className="w-4 h-4 text-accent-purple" />
            <span className="font-medium text-sm text-text-primary">Test Execution Summary</span>
          </div>
          <div className="prose prose-sm max-w-none text-text-secondary prose-headings:text-text-primary prose-strong:text-text-primary prose-code:bg-bg-tertiary prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-accent-purple prose-code:before:content-none prose-code:after:content-none">
            <ReactMarkdown>{session.summary}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}
