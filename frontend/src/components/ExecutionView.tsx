import { useState, useRef, useEffect } from 'react';
import {
  Bot, User, Wrench, AlertCircle, CheckCircle, Loader2,
  Monitor, Maximize2, Minimize2, Camera, MousePointer,
  Keyboard, Eye, ArrowRight, Clock, Activity, Home
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { ExecutionMessage, TestCase, FlowGraph, PageData } from '@/types';
import { PageTree } from './PageTree';
import clsx from 'clsx';

interface ExecutionViewProps {
  messages: ExecutionMessage[];
  tests: TestCase[];
  targetUrl: string;
  status: 'idle' | 'running' | 'complete' | 'error';
  flowGraph?: FlowGraph;
  pages?: PageData[];
  onBackToHome: () => void;
}

export function ExecutionView({ messages, tests, targetUrl, status, flowGraph, pages, onBackToHome }: ExecutionViewProps) {
  const [vncExpanded, setVncExpanded] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // VNC URL - connects to the noVNC server
  const vncUrl = `${window.location.protocol}//${window.location.hostname}:6080/vnc.html?autoconnect=true&resize=scale&quality=6`;

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="animate-fade-in flex h-screen w-screen fixed inset-0 bg-bg-secondary">
      {/* Left Panel - Page Structure */}
      <div className="w-56 flex-shrink-0 bg-bg-primary border-r border-border flex flex-col">
        {/* Back to Home Button */}
        <div className="p-3 border-b border-border">
          <button
            onClick={onBackToHome}
            className="flex items-center gap-2 w-full px-3 py-2 bg-bg-tertiary hover:bg-accent-light border border-border rounded-lg transition-all text-sm font-medium text-text-secondary hover:text-accent-primary hover:border-accent-primary group"
          >
            <Home className="w-4 h-4 group-hover:text-accent-primary transition-colors" />
            <span>Back to Home</span>
          </button>
        </div>

        {/* Page Tree */}
        {flowGraph && pages && (
          <div className="flex-1 overflow-hidden min-h-0">
            <PageTree flowGraph={flowGraph} pages={pages} baseUrl={targetUrl} />
          </div>
        )}
      </div>

      {/* Main Content - Virtual Desktop */}
      <div className="flex-1 flex flex-col min-w-0 p-4">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 rounded-lg bg-accent-light">
            <Activity className="w-3.5 h-3.5 text-accent-primary" />
          </div>
          <h2 className="text-sm font-semibold text-text-primary">
            Test Execution
          </h2>
        </div>

        {/* Status Banner */}
        <div className={clsx(
          'mb-3 px-3 py-2 rounded-lg border',
          status === 'running' && 'bg-accent-cyan/15 border-accent-cyan/30',
          status === 'complete' && 'bg-accent-green/15 border-accent-green/30',
          status === 'error' && 'bg-accent-red/15 border-accent-red/30',
          status === 'idle' && 'bg-bg-tertiary border-border',
        )}>
          <div className="flex items-center gap-2">
            {status === 'running' && (
              <>
                <Loader2 className="w-3.5 h-3.5 text-accent-cyan animate-spin" />
                <span className="text-accent-cyan font-medium text-xs">
                  Executing {tests.length} test cases on {targetUrl}
                </span>
              </>
            )}
            {status === 'complete' && (
              <>
                <CheckCircle className="w-3.5 h-3.5 text-accent-green" />
                <span className="text-accent-green font-medium text-xs">Execution Complete</span>
              </>
            )}
            {status === 'error' && (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-accent-red" />
                <span className="text-accent-red font-medium text-xs">Execution Failed</span>
              </>
            )}
            {status === 'idle' && (
              <>
                <Loader2 className="w-3.5 h-3.5 text-text-secondary animate-spin" />
                <span className="text-text-secondary font-medium text-xs">Starting...</span>
              </>
            )}
          </div>
        </div>

        {/* VNC Viewer - Takes full remaining height */}
        <div className="flex-1 bg-bg-tertiary border border-border rounded-lg overflow-hidden shadow-soft flex flex-col min-h-0">
          <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-bg-hover">
            <div className="flex items-center gap-2">
              <Monitor className="w-3.5 h-3.5 text-accent-primary" />
              <span className="font-medium text-xs text-text-primary">Virtual Desktop</span>
              <span className="text-[9px] text-accent-green bg-accent-green/15 px-1.5 py-0.5 rounded font-medium uppercase tracking-wide animate-pulse">Live</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setVncExpanded(!vncExpanded)}
                className="p-1 hover:bg-bg-tertiary rounded transition-colors"
              >
                {vncExpanded ? (
                  <Minimize2 className="w-3 h-3 text-text-tertiary" />
                ) : (
                  <Maximize2 className="w-3 h-3 text-text-tertiary" />
                )}
              </button>
              <a
                href={vncUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] text-accent-primary hover:underline"
              >
                Open in new tab
              </a>
            </div>
          </div>
          {vncExpanded && (
            <div className="flex-1 relative bg-bg-primary min-h-[300px]">
              <iframe
                src={vncUrl}
                className="absolute inset-0 w-full h-full border-0"
                title="Virtual Desktop"
                allow="clipboard-read; clipboard-write"
              />
            </div>
          )}
        </div>
      </div>

      {/* Agent Trail - Fixed Right Sidebar */}
      <div className="w-72 flex-shrink-0 bg-bg-primary border-l border-border overflow-hidden flex flex-col">
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border bg-bg-hover">
          <Bot className="w-3.5 h-3.5 text-accent-purple" />
          <span className="font-medium text-xs text-text-primary">Agent Trail</span>
          <span className="text-[10px] text-text-tertiary ml-auto bg-bg-tertiary px-1.5 py-0.5 rounded-full">{messages.length} events</span>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-bg-secondary/30">
          {messages.length === 0 ? (
            <div className="text-center text-text-secondary py-8">
              <Bot className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="font-medium text-sm">Waiting for agent activity...</p>
              <p className="text-xs mt-1 text-text-tertiary">The agent will start interacting with the browser shortly</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <TrailItem key={index} message={msg} index={index} />
            ))
          )}
          <div ref={messagesEndRef} />

          {status === 'running' && messages.length > 0 && (
            <div className="flex items-center gap-2 text-accent-primary text-sm p-3 bg-accent-light rounded-lg border border-accent-primary/20">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Agent is working...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TrailItem({ message, index }: { message: ExecutionMessage; index: number }) {
  const [imageExpanded, setImageExpanded] = useState(true);

  // Status message
  if (message.type === 'status') {
    return (
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-accent-cyan/15 flex items-center justify-center">
          <Clock className="w-3.5 h-3.5 text-accent-cyan" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] text-text-tertiary mb-0.5 uppercase tracking-wide">Status Update</div>
          <div className="text-sm text-accent-cyan">{message.message}</div>
        </div>
      </div>
    );
  }

  // Error message
  if (message.type === 'error') {
    return (
      <div className="p-3 bg-accent-red/15 border border-accent-red/30 rounded-xl">
        <div className="flex items-center gap-2 mb-1">
          <AlertCircle className="w-3.5 h-3.5 text-accent-red" />
          <span className="text-[10px] font-medium text-accent-red uppercase tracking-wide">Error</span>
        </div>
        <div className="text-sm text-accent-red">{message.message}</div>
      </div>
    );
  }

  // Agent thinking/message
  if (message.type === 'message') {
    const isAssistant = message.role === 'assistant';
    return (
      <div className="flex items-start gap-3">
        <div className={clsx(
          'flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center',
          isAssistant ? 'bg-accent-purple/15' : 'bg-accent-cyan/15'
        )}>
          {isAssistant ? (
            <Bot className="w-3.5 h-3.5 text-accent-purple" />
          ) : (
            <User className="w-3.5 h-3.5 text-accent-cyan" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] text-text-tertiary mb-0.5 uppercase tracking-wide">
            {isAssistant ? 'Agent Thinking' : 'User Input'}
          </div>
          <div className="text-sm text-text-primary bg-bg-tertiary border border-border p-3 rounded-lg overflow-hidden">
            <div className="prose prose-sm max-w-none prose-invert prose-headings:text-text-primary prose-headings:font-semibold prose-headings:mt-3 prose-headings:mb-2 prose-p:my-1.5 prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5 prose-strong:text-text-primary prose-code:bg-bg-hover prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-accent-purple prose-code:text-xs prose-code:before:content-none prose-code:after:content-none prose-pre:bg-bg-hover prose-pre:p-2 prose-pre:rounded-lg prose-pre:my-2">
              <ReactMarkdown>{message.content || ''}</ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Tool use (action being taken)
  if (message.type === 'tool_use') {
    const toolName = message.name || '';
    const input = message.input || {};

    // Determine icon based on action
    let Icon = Wrench;
    let actionLabel = toolName;
    let actionDetail = '';

    if (toolName === 'computer') {
      const action = input.action as string;
      if (action === 'screenshot') {
        Icon = Camera;
        actionLabel = 'Taking Screenshot';
      } else if (action === 'left_click' || action === 'click' || action === 'right_click' || action === 'double_click') {
        Icon = MousePointer;
        actionLabel = `${action.replace('_', ' ')}`;
        if (input.coordinate) {
          actionDetail = `at (${(input.coordinate as number[])[0]}, ${(input.coordinate as number[])[1]})`;
        }
      } else if (action === 'type' || action === 'key') {
        Icon = Keyboard;
        actionLabel = action === 'type' ? 'Typing' : 'Key Press';
        actionDetail = input.text as string || input.key as string || '';
      } else if (action === 'scroll') {
        Icon = ArrowRight;
        actionLabel = 'Scrolling';
        actionDetail = `${input.coordinate ? `at (${(input.coordinate as number[])[0]}, ${(input.coordinate as number[])[1]})` : ''} ${input.direction || ''}`;
      } else {
        actionLabel = action || 'Computer Action';
      }
    } else if (toolName === 'bash') {
      Icon = Wrench;
      actionLabel = 'Running Command';
      actionDetail = input.command as string || '';
    }

    return (
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-accent-yellow/15 flex items-center justify-center">
          <Icon className="w-3.5 h-3.5 text-accent-yellow" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-[10px] font-medium text-accent-yellow uppercase tracking-wide">{actionLabel}</span>
            {actionDetail && (
              <code className="text-[10px] bg-accent-yellow/15 text-accent-yellow px-1.5 py-0.5 rounded truncate max-w-[180px]">
                {actionDetail}
              </code>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Tool result (with potential screenshot)
  if (message.type === 'tool_result') {
    const hasScreenshot = !!message.screenshot;
    const hasOutput = !!message.output;
    const hasError = !!message.error;

    return (
      <div className="flex items-start gap-3">
        <div className={clsx(
          'flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center',
          hasError ? 'bg-accent-red/15' : hasScreenshot ? 'bg-accent-green/15' : 'bg-accent-cyan/15'
        )}>
          {hasError ? (
            <AlertCircle className="w-3.5 h-3.5 text-accent-red" />
          ) : hasScreenshot ? (
            <Eye className="w-3.5 h-3.5 text-accent-green" />
          ) : (
            <CheckCircle className="w-3.5 h-3.5 text-accent-cyan" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] text-text-tertiary mb-0.5 uppercase tracking-wide">
            {hasError ? 'Error' : hasScreenshot ? 'Screen Capture' : 'Result'}
          </div>

          {/* Output text */}
          {hasOutput && (
            <pre className="text-xs text-text-secondary bg-bg-tertiary border border-border p-2 rounded mb-2 overflow-x-auto max-h-20 font-mono">
              {message.output}
            </pre>
          )}

          {/* Error */}
          {hasError && (
            <div className="text-sm text-accent-red bg-accent-red/15 border border-accent-red/30 p-2 rounded mb-2">
              {message.error}
            </div>
          )}

          {/* Screenshot */}
          {hasScreenshot && (
            <div className="relative">
              <button
                onClick={() => setImageExpanded(!imageExpanded)}
                className="flex items-center gap-1 text-xs text-accent-primary mb-2 hover:underline"
              >
                <Camera className="w-3 h-3" />
                {imageExpanded ? 'Hide screenshot' : 'Show screenshot'}
              </button>
              {imageExpanded && (
                <div className="relative group">
                  <img
                    src={`data:image/png;base64,${message.screenshot}`}
                    alt="Screenshot"
                    className="w-full rounded-lg border border-border cursor-pointer hover:border-accent-primary transition-colors"
                    onClick={() => {
                      // Open in new tab for full view
                      const newTab = window.open();
                      if (newTab) {
                        newTab.document.write(`<img src="data:image/png;base64,${message.screenshot}" style="max-width:100%"/>`);
                      }
                    }}
                  />
                  <div className="absolute bottom-2 right-2 text-[10px] bg-black/60 text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                    Click to enlarge
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
}
