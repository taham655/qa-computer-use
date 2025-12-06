import { useState, useEffect } from 'react';
import { Home, Play, FlaskConical, ChevronLeft, ChevronRight, Search, Settings, FileText, HelpCircle } from 'lucide-react';
import clsx from 'clsx';

export type NavPage = 'home' | 'run-test';

interface NavSidebarProps {
  activePage: NavPage;
  onNavigate: (page: NavPage) => void;
}

export function NavSidebar({ activePage, onNavigate }: NavSidebarProps) {
  const [isExpanded, setIsExpanded] = useState(() => {
    const saved = localStorage.getItem('sidebar_expanded');
    return saved !== null ? JSON.parse(saved) : true;
  });

  useEffect(() => {
    localStorage.setItem('sidebar_expanded', JSON.stringify(isExpanded));
  }, [isExpanded]);

  return (
    <aside
      className={clsx(
        'bg-bg-primary border-r border-border flex flex-col min-h-screen transition-all duration-300 ease-in-out shadow-sidebar relative',
        isExpanded ? 'w-64' : 'w-[72px]'
      )}
    >
      {/* Logo Section */}
      <div className={clsx(
        'flex items-center gap-3 px-4 py-5 border-b border-border',
        !isExpanded && 'justify-center'
      )}>
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-indigo to-accent-purple flex items-center justify-center flex-shrink-0 shadow-soft">
          <FlaskConical className="w-5 h-5 text-bg-primary" />
        </div>
        {isExpanded && (
          <div className="animate-slide-in overflow-hidden">
            <span className="font-semibold text-text-primary text-base whitespace-nowrap">RoverQA</span>
          </div>
        )}
      </div>

      {/* Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={clsx(
          'absolute top-20 -right-3 w-6 h-6 bg-bg-tertiary border border-border rounded-full flex items-center justify-center',
          'hover:bg-accent-light hover:border-accent-primary hover:text-accent-primary',
          'transition-all duration-200 shadow-soft z-10'
        )}
      >
        {isExpanded ? (
          <ChevronLeft className="w-3.5 h-3.5" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5" />
        )}
      </button>

      {/* Main Navigation */}
      <nav className="flex-1 px-3 py-4">
        <div className="space-y-1">
          <NavItem
            icon={<Home className="w-5 h-5" />}
            label="Home"
            active={activePage === 'home'}
            onClick={() => onNavigate('home')}
            expanded={isExpanded}
          />
          <NavItem
            icon={<Play className="w-5 h-5" />}
            label="Run Test"
            active={activePage === 'run-test'}
            onClick={() => onNavigate('run-test')}
            expanded={isExpanded}
          />
        </div>

        {/* Divider */}
        <div className="my-4 border-t border-border" />

        {/* Secondary Navigation */}
        <div className={clsx(
          'mb-2',
          isExpanded ? 'px-3' : 'px-2 text-center'
        )}>
          <span className={clsx(
            'text-[11px] font-medium text-text-tertiary uppercase tracking-wider',
            !isExpanded && 'hidden'
          )}>
            Quick Access
          </span>
        </div>
        <div className="space-y-1">
          <NavItem
            icon={<Search className="w-5 h-5" />}
            label="Search"
            active={false}
            onClick={() => {}}
            expanded={isExpanded}
            disabled
          />
          <NavItem
            icon={<FileText className="w-5 h-5" />}
            label="Documentation"
            active={false}
            onClick={() => {}}
            expanded={isExpanded}
            disabled
          />
        </div>
      </nav>

      {/* Bottom Section */}
      <div className="border-t border-border px-3 py-4">
        <div className="space-y-1">
          <NavItem
            icon={<Settings className="w-5 h-5" />}
            label="Settings"
            active={false}
            onClick={() => {}}
            expanded={isExpanded}
            disabled
          />
          <NavItem
            icon={<HelpCircle className="w-5 h-5" />}
            label="Help"
            active={false}
            onClick={() => {}}
            expanded={isExpanded}
            disabled
          />
        </div>
      </div>
    </aside>
  );
}

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
  expanded: boolean;
  disabled?: boolean;
}

function NavItem({ icon, label, active, onClick, expanded, disabled }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        'group flex items-center gap-3 w-full rounded-xl transition-all duration-200',
        expanded ? 'px-3 py-2.5' : 'px-0 py-2.5 justify-center',
        active && 'bg-accent-light text-accent-primary',
        !active && !disabled && 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary',
        disabled && 'text-text-tertiary cursor-not-allowed opacity-50'
      )}
      title={!expanded ? label : undefined}
    >
      <div
        className={clsx(
          'flex-shrink-0 transition-all duration-200',
          active && 'text-accent-primary'
        )}
      >
        {icon}
      </div>
      {expanded && (
        <span className={clsx(
          'text-sm font-medium whitespace-nowrap animate-slide-in',
          active && 'text-accent-primary'
        )}>
          {label}
        </span>
      )}
      {active && expanded && (
        <div className="ml-auto w-1.5 h-1.5 rounded-full bg-accent-primary" />
      )}
    </button>
  );
}
