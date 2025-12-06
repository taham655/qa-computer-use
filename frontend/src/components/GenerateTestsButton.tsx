import { Bot, Sparkles } from 'lucide-react';
import clsx from 'clsx';

interface GenerateTestsButtonProps {
  onClick: () => void;
  loading: boolean;
  disabled: boolean;
}

export function GenerateTestsButton({ onClick, loading, disabled }: GenerateTestsButtonProps) {
  return (
    <section className="mb-8 animate-slide-up" style={{ animationDelay: '250ms' }}>
      <button
        onClick={onClick}
        disabled={loading || disabled}
        className={clsx(
          'w-full flex items-center justify-center gap-3 py-4 rounded-xl font-semibold transition-all',
          loading || disabled
            ? 'bg-bg-tertiary text-text-tertiary cursor-not-allowed border border-border'
            : 'bg-gradient-to-r from-accent-indigo to-accent-purple text-bg-primary hover:shadow-lg hover:shadow-accent-indigo/20 hover:-translate-y-0.5'
        )}
      >
        {loading ? (
          <>
            <div className="spinner" />
            <span className="text-sm">AI is generating test cases...</span>
          </>
        ) : (
          <>
            <Bot className="w-5 h-5" />
            <span>Generate Test Cases with AI</span>
            <Sparkles className="w-4 h-4" />
          </>
        )}
      </button>
    </section>
  );
}
