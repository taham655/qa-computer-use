import { FlaskConical, Sparkles } from 'lucide-react';

export function Header() {
  return (
    <header className="mb-8 animate-fade-in">
      <div className="flex items-center gap-4 mb-3">
        <div className="p-3 rounded-2xl bg-gradient-to-br from-accent-indigo/10 to-accent-purple/10 border border-accent-indigo/20">
          <FlaskConical className="w-7 h-7 text-accent-indigo" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-2">
            RoverQA
            <Sparkles className="w-5 h-5 text-accent-yellow" />
          </h1>
          <p className="text-text-secondary text-sm mt-0.5">
            Crawl websites, generate flow graphs, and create comprehensive test cases
          </p>
        </div>
      </div>
    </header>
  );
}
