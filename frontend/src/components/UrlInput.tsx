import { useState } from 'react';
import { Link, Rocket, Globe } from 'lucide-react';
import clsx from 'clsx';

interface UrlInputProps {
  onCrawl: (url: string) => void;
  loading: boolean;
}

export function UrlInput({ onCrawl, loading }: UrlInputProps) {
  const [url, setUrl] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url && !loading) {
      onCrawl(url);
    }
  };

  return (
    <section className="mb-8 animate-slide-up">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 rounded-lg bg-accent-light">
          <Globe className="w-4 h-4 text-accent-primary" />
        </div>
        <h2 className="text-base font-semibold text-text-primary">
          Enter URL to Test
        </h2>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="flex-1 relative">
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-text-tertiary">
            <Link className="w-4 h-4" />
          </div>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            required
            className="w-full bg-bg-tertiary border border-border rounded-xl pl-11 pr-4 py-3 text-sm text-text-primary focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20 transition-all placeholder:text-text-tertiary"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !url}
          className={clsx(
            'flex items-center gap-2 px-5 py-3 rounded-xl font-medium transition-all text-sm',
            loading || !url
              ? 'bg-bg-tertiary text-text-tertiary cursor-not-allowed border border-border'
              : 'bg-accent-primary text-bg-primary hover:bg-accent-secondary shadow-soft hover:shadow-card'
          )}
        >
          {loading ? (
            <>
              <div className="spinner" />
              Crawling...
            </>
          ) : (
            <>
              <Rocket className="w-4 h-4" />
              Start Crawl
            </>
          )}
        </button>
      </form>
    </section>
  );
}
