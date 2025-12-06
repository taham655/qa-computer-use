import { Settings, RotateCcw, ChevronRight, ChevronLeft, Sliders } from 'lucide-react';
import { useState } from 'react';

interface ConfigPanelProps {
  settings: {
    maxPages: number;
    maxDepth: number;
    extractStructure: boolean;
    testTypes: string[];
    maxTests: number;
  };
  onSettingsChange: (key: string, value: unknown) => void;
  onReset: () => void;
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

export function ConfigPanel({
  settings,
  onSettingsChange,
  onReset,
}: ConfigPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (isCollapsed) {
    return (
      <aside className="w-14 bg-bg-primary border-l border-border flex flex-col items-center py-6 min-h-screen shadow-sidebar">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-2.5 rounded-xl bg-bg-tertiary hover:bg-accent-light hover:text-accent-primary transition-colors"
          title="Expand Configuration"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <div className="mt-4 p-2.5 rounded-xl bg-bg-tertiary">
          <Sliders className="w-4 h-4 text-text-tertiary" />
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-80 bg-bg-primary border-l border-border p-5 flex flex-col min-h-screen relative shadow-sidebar">
      {/* Collapse Button */}
      <button
        onClick={() => setIsCollapsed(true)}
        className="absolute top-6 left-0 -translate-x-1/2 p-1.5 rounded-full bg-bg-tertiary border border-border hover:border-accent-primary hover:text-accent-primary transition-colors z-10 shadow-soft"
        title="Collapse Configuration"
      >
        <ChevronRight className="w-3.5 h-3.5" />
      </button>

      <div className="flex items-center gap-2.5 mb-6">
        <div className="p-2 rounded-lg bg-accent-light">
          <Settings className="w-4 h-4 text-accent-primary" />
        </div>
        <h2 className="text-base font-semibold text-text-primary">Configuration</h2>
      </div>

      {/* Crawl Settings */}
      <section className="mb-5">
        <h3 className="text-xs font-medium text-text-tertiary uppercase tracking-wider mb-3">
          Crawl Settings
        </h3>

        <label className="block mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-sm text-text-secondary">Max Pages</span>
            <span className="text-sm font-mono font-medium text-accent-primary bg-accent-light px-2 py-0.5 rounded">
              {settings.maxPages}
            </span>
          </div>
          <input
            type="range"
            min={5}
            max={100}
            value={settings.maxPages}
            onChange={(e) => onSettingsChange('maxPages', Number(e.target.value))}
            className="w-full"
          />
        </label>

        <label className="block mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-sm text-text-secondary">Max Depth</span>
            <span className="text-sm font-mono font-medium text-accent-primary bg-accent-light px-2 py-0.5 rounded">
              {settings.maxDepth}
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={5}
            value={settings.maxDepth}
            onChange={(e) => onSettingsChange('maxDepth', Number(e.target.value))}
            className="w-full"
          />
        </label>

        <label className="flex items-center gap-2.5 cursor-pointer group">
          <input
            type="checkbox"
            checked={settings.extractStructure}
            onChange={(e) => onSettingsChange('extractStructure', e.target.checked)}
          />
          <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">
            Extract Page Structure
          </span>
        </label>
      </section>

      <hr className="border-border mb-5" />

      {/* Test Generation */}
      <section className="mb-5 flex-1">
        <h3 className="text-xs font-medium text-text-tertiary uppercase tracking-wider mb-3">
          Test Generation
        </h3>

        <label className="block mb-4">
          <span className="text-sm text-text-secondary mb-2 block">Test Types</span>
          <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
            {TEST_TYPES.map((type) => (
              <label key={type} className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={settings.testTypes.includes(type)}
                  onChange={(e) => {
                    const newTypes = e.target.checked
                      ? [...settings.testTypes, type]
                      : settings.testTypes.filter((t) => t !== type);
                    onSettingsChange('testTypes', newTypes);
                  }}
                />
                <span className="text-xs text-text-secondary group-hover:text-text-primary transition-colors capitalize">
                  {type.replace('_', ' ')}
                </span>
              </label>
            ))}
          </div>
        </label>

        <label className="block">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-sm text-text-secondary">Max Tests</span>
            <span className="text-sm font-mono font-medium text-accent-primary bg-accent-light px-2 py-0.5 rounded">
              {settings.maxTests}
            </span>
          </div>
          <input
            type="range"
            min={5}
            max={50}
            value={settings.maxTests}
            onChange={(e) => onSettingsChange('maxTests', Number(e.target.value))}
            className="w-full"
          />
        </label>
      </section>

      <hr className="border-border mb-5" />

      {/* Actions */}
      <div className="mt-auto">
        <button
          onClick={onReset}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-bg-tertiary border border-border rounded-xl text-text-secondary hover:border-accent-red hover:text-accent-red hover:bg-accent-red/10 transition-all text-sm font-medium"
        >
          <RotateCcw className="w-4 h-4" />
          Reset All
        </button>
      </div>
    </aside>
  );
}
