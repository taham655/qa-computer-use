import clsx from 'clsx';

interface StatsCardProps {
  value: number | string;
  label: string;
  delay?: number;
}

export function StatsCard({ value, label, delay = 0 }: StatsCardProps) {
  return (
    <div
      className={clsx(
        'bg-bg-tertiary border border-border rounded-xl p-4 text-center',
        'transition-all duration-200 hover:border-accent-primary hover:shadow-card',
        'animate-slide-up'
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="text-2xl font-semibold text-accent-primary mb-1">
        {value}
      </div>
      <div className="text-xs text-text-secondary uppercase tracking-wide">
        {label}
      </div>
    </div>
  );
}
