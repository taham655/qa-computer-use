import { useState } from 'react';
import { BarChart3, ChevronDown, ChevronRight, FileText, MousePointerClick, Link2, FormInput } from 'lucide-react';
import { StatsCard } from './StatsCard';
import type { CrawlStats, PageData } from '@/types';

interface CrawlResultsProps {
  stats: CrawlStats;
  pages: PageData[];
}

export function CrawlResults({ stats, pages }: CrawlResultsProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <section className="mb-8 animate-slide-up" style={{ animationDelay: '100ms' }}>
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 rounded-lg bg-accent-green/15">
          <BarChart3 className="w-4 h-4 text-accent-green" />
        </div>
        <h2 className="text-base font-semibold text-text-primary">
          Crawl Results
        </h2>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        <StatsCard value={stats.pages_found} label="Pages Found" delay={0} />
        <StatsCard value={stats.total_links} label="Total Links" delay={100} />
        <StatsCard value={stats.forms_found} label="Forms Found" delay={200} />
        <StatsCard value={stats.interactive_elements} label="Interactive" delay={300} />
      </div>

      {/* Pages Accordion */}
      <div className="bg-bg-tertiary border border-border rounded-xl overflow-hidden shadow-soft">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between p-4 hover:bg-bg-hover transition-colors"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-accent-primary" />
            <span className="font-medium text-sm text-text-primary">Pages Discovered</span>
            <span className="text-text-tertiary text-xs bg-bg-hover px-2 py-0.5 rounded-full">
              {pages.length}
            </span>
          </div>
          {expanded ? (
            <ChevronDown className="w-4 h-4 text-text-tertiary" />
          ) : (
            <ChevronRight className="w-4 h-4 text-text-tertiary" />
          )}
        </button>

        {expanded && (
          <div className="border-t border-border max-h-72 overflow-y-auto">
            {pages.map((page, index) => (
              <PageItem key={index} page={page} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function PageItem({ page }: { page: PageData }) {
  return (
    <div className="p-4 border-b border-border last:border-b-0 hover:bg-bg-hover transition-colors">
      <div className="font-medium text-sm text-text-primary mb-1 truncate">
        {page.title || 'Untitled'}
      </div>
      <div className="text-xs text-text-secondary truncate mb-2">
        {page.url}
      </div>
      <div className="flex items-center gap-4 text-xs text-text-tertiary">
        <span className="flex items-center gap-1">
          <MousePointerClick className="w-3 h-3" />
          {page.buttons_count} buttons
        </span>
        <span className="flex items-center gap-1">
          <FormInput className="w-3 h-3" />
          {page.forms_count} forms
        </span>
        <span className="flex items-center gap-1">
          <Link2 className="w-3 h-3" />
          {page.links_count} links
        </span>
      </div>
    </div>
  );
}
