import { Settings, Check, X, RotateCcw, ArrowLeft } from 'lucide-react';
import type { APIKeyStatus, ViewMode } from '@/types';
import clsx from 'clsx';

interface SidebarProps {
  keyStatus: APIKeyStatus | null;
  settings: {
    maxPages: number;
    maxDepth: number;
    extractStructure: boolean;
    testTypes: string[];
    maxTests: number;
    aiProvider: string;
  };
  onSettingsChange: (key: string, value: unknown) => void;
  onReset: () => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}

const TEST_TYPES = [
  'happy_path',
  'edge_case',
  'error_handling',
  'boundary',
  'security',
  'accessibility',
  'performance',
];

export function Sidebar({
  keyStatus,
  settings,
  onSettingsChange,
  onReset,
  viewMode,
  onViewModeChange,
}: SidebarProps) {
  return (
    <aside className="w-72 bg-bg-secondary border-r border-border p-6 flex flex-col min-h-screen">
      <div className="flex items-center gap-2 mb-6">
        <Settings className="w-5 h-5 text-accent-cyan" />
        <h2 className="text-lg font-semibold">Configuration</h2>
      </div>

      {/* API Keys */}
      <section className="mb-6">
        <h3 className="text-sm font-medium text-text-secondary uppercase tracking-wider mb-3">
          API Keys
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <KeyStatusBadge label="Firecrawl" active={keyStatus?.firecrawl ?? false} />
          <KeyStatusBadge
            label={keyStatus?.openai ? 'OpenAI' : keyStatus?.anthropic ? 'Anthropic' : 'AI API'}
            active={(keyStatus?.openai || keyStatus?.anthropic) ?? false}
          />
        </div>
      </section>

      <hr className="border-border mb-6" />

      {/* Crawl Settings */}
      <section className="mb-6">
        <h3 className="text-sm font-medium text-text-secondary uppercase tracking-wider mb-3">
          Crawl Settings
        </h3>

        <label className="block mb-4">
          <span className="text-sm text-text-secondary">Max Pages</span>
          <input
            type="range"
            min={5}
            max={100}
            value={settings.maxPages}
            onChange={(e) => onSettingsChange('maxPages', Number(e.target.value))}
            className="w-full mt-1 accent-accent-cyan"
          />
          <span className="text-sm font-mono text-accent-cyan">{settings.maxPages}</span>
        </label>

        <label className="block mb-4">
          <span className="text-sm text-text-secondary">Max Depth</span>
          <input
            type="range"
            min={1}
            max={5}
            value={settings.maxDepth}
            onChange={(e) => onSettingsChange('maxDepth', Number(e.target.value))}
            className="w-full mt-1 accent-accent-cyan"
          />
          <span className="text-sm font-mono text-accent-cyan">{settings.maxDepth}</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.extractStructure}
            onChange={(e) => onSettingsChange('extractStructure', e.target.checked)}
            className="w-4 h-4 accent-accent-cyan rounded"
          />
          <span className="text-sm text-text-secondary">Extract Page Structure</span>
        </label>
      </section>

      <hr className="border-border mb-6" />

      {/* Test Generation */}
      <section className="mb-6">
        <h3 className="text-sm font-medium text-text-secondary uppercase tracking-wider mb-3">
          Test Generation
        </h3>

        <label className="block mb-4">
          <span className="text-sm text-text-secondary mb-2 block">Test Types</span>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {TEST_TYPES.map((type) => (
              <label key={type} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.testTypes.includes(type)}
                  onChange={(e) => {
                    const newTypes = e.target.checked
                      ? [...settings.testTypes, type]
                      : settings.testTypes.filter((t) => t !== type);
                    onSettingsChange('testTypes', newTypes);
                  }}
                  className="w-3 h-3 accent-accent-cyan rounded"
                />
                <span className="text-xs text-text-secondary">{type.replace('_', ' ')}</span>
              </label>
            ))}
          </div>
        </label>

        <label className="block mb-4">
          <span className="text-sm text-text-secondary">Max Tests</span>
          <input
            type="range"
            min={5}
            max={50}
            value={settings.maxTests}
            onChange={(e) => onSettingsChange('maxTests', Number(e.target.value))}
            className="w-full mt-1 accent-accent-cyan"
          />
          <span className="text-sm font-mono text-accent-cyan">{settings.maxTests}</span>
        </label>

        <label className="block">
          <span className="text-sm text-text-secondary">AI Provider</span>
          <select
            value={settings.aiProvider}
            onChange={(e) => onSettingsChange('aiProvider', e.target.value)}
            className="w-full mt-1 bg-bg-tertiary border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent-cyan"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
          </select>
        </label>
      </section>

      <hr className="border-border mb-6" />

      {/* Actions */}
      <div className="mt-auto space-y-3">
        {viewMode === 'execution' && (
          <button
            onClick={() => onViewModeChange('setup')}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-bg-tertiary border border-border rounded-lg hover:border-accent-cyan transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Setup
          </button>
        )}
        <button
          onClick={onReset}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-bg-tertiary border border-border rounded-lg hover:border-accent-red hover:text-accent-red transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Reset All
        </button>
      </div>
    </aside>
  );
}

function KeyStatusBadge({ label, active }: { label: string; active: boolean }) {
  return (
    <div
      className={clsx(
        'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium',
        active
          ? 'bg-accent-green/10 text-accent-green border border-accent-green/30'
          : 'bg-accent-red/10 text-accent-red border border-accent-red/30'
      )}
    >
      {active ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
      {label}
    </div>
  );
}
