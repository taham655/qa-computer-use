import { useState } from 'react';
import {
  FolderOpen, Folder, FileText, Home as HomeIcon,
  ChevronDown, ChevronRight, Globe, FormInput,
  MousePointerClick, Link as LinkIcon
} from 'lucide-react';
import clsx from 'clsx';
import type { FlowGraph, PageData } from '@/types';

interface PageTreeProps {
  flowGraph: FlowGraph;
  pages: PageData[];
  baseUrl: string;
}

interface TreeNode {
  name: string;
  path: string;
  url: string;
  isRoot: boolean;
  children: TreeNode[];
  pageData?: PageData;
}

function buildTree(pages: PageData[], baseUrl: string): TreeNode {
  const root: TreeNode = {
    name: new URL(baseUrl).hostname,
    path: '/',
    url: baseUrl,
    isRoot: true,
    children: [],
  };

  // Parse URLs and build tree structure
  const pathMap = new Map<string, TreeNode>();
  pathMap.set('/', root);

  pages.forEach((page) => {
    try {
      const url = new URL(page.url);
      const pathParts = url.pathname.split('/').filter(Boolean);

      let currentPath = '';
      let currentNode = root;

      pathParts.forEach((part, index) => {
        currentPath += '/' + part;

        if (!pathMap.has(currentPath)) {
          const isLastPart = index === pathParts.length - 1;
          const newNode: TreeNode = {
            name: part,
            path: currentPath,
            url: page.url,
            isRoot: false,
            children: [],
            pageData: isLastPart ? page : undefined,
          };
          pathMap.set(currentPath, newNode);
          currentNode.children.push(newNode);
        }
        currentNode = pathMap.get(currentPath)!;
      });

      // Handle root pages (no path)
      if (pathParts.length === 0) {
        root.pageData = page;
      }
    } catch {
      // Invalid URL, skip
    }
  });

  return root;
}

export function PageTree({ flowGraph, pages, baseUrl }: PageTreeProps) {
  const tree = buildTree(pages, baseUrl);
  const nodeCount = Object.keys(flowGraph.nodes).length;
  const edgeCount = flowGraph.edges.length;

  return (
    <div className="h-full flex flex-col bg-bg-secondary/50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border bg-bg-primary">
        <Globe className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
        <span className="font-medium text-xs text-text-primary">Site Structure</span>
        <span className="text-[10px] text-text-tertiary ml-auto bg-bg-tertiary px-1.5 py-0.5 rounded-full flex-shrink-0">
          {nodeCount} pages
        </span>
      </div>

      {/* Stats Bar */}
      <div className="flex gap-3 px-3 py-2 bg-bg-tertiary border-b border-border">
        <div className="flex items-center gap-1 text-[10px] text-text-secondary">
          <FileText className="w-3 h-3 text-accent-cyan" />
          <span>{nodeCount} pages</span>
        </div>
        <div className="flex items-center gap-1 text-[10px] text-text-secondary">
          <LinkIcon className="w-3 h-3 text-accent-purple" />
          <span>{edgeCount} links</span>
        </div>
      </div>

      {/* Tree View */}
      <div className="flex-1 overflow-y-auto p-2">
        <TreeNodeItem node={tree} level={0} />
      </div>
    </div>
  );
}

interface TreeNodeItemProps {
  node: TreeNode;
  level: number;
}

function TreeNodeItem({ node, level }: TreeNodeItemProps) {
  const [isExpanded, setIsExpanded] = useState(level < 2);
  const hasChildren = node.children.length > 0;
  const hasPageData = !!node.pageData;

  return (
    <div className="select-none">
      <div
        className={clsx(
          'flex items-center gap-1 py-1 px-1.5 rounded cursor-pointer transition-colors group',
          'hover:bg-bg-tertiary hover:shadow-soft'
        )}
        style={{ paddingLeft: `${level * 10 + 4}px` }}
        onClick={() => hasChildren && setIsExpanded(!isExpanded)}
      >
        {/* Expand/Collapse Icon */}
        <div className="w-3.5 h-3.5 flex items-center justify-center flex-shrink-0">
          {hasChildren ? (
            isExpanded ? (
              <ChevronDown className="w-2.5 h-2.5 text-text-tertiary" />
            ) : (
              <ChevronRight className="w-2.5 h-2.5 text-text-tertiary" />
            )
          ) : (
            <span className="w-2.5" />
          )}
        </div>

        {/* Icon */}
        {node.isRoot ? (
          <HomeIcon className="w-3.5 h-3.5 text-accent-primary flex-shrink-0" />
        ) : hasChildren ? (
          isExpanded ? (
            <FolderOpen className="w-3.5 h-3.5 text-accent-yellow flex-shrink-0" />
          ) : (
            <Folder className="w-3.5 h-3.5 text-accent-yellow flex-shrink-0" />
          )
        ) : (
          <FileText className="w-3.5 h-3.5 text-accent-cyan flex-shrink-0" />
        )}

        {/* Label */}
        <span className={clsx(
          'text-xs truncate flex-1 min-w-0',
          node.isRoot ? 'font-medium text-text-primary' : 'text-text-secondary'
        )}>
          {node.name}
        </span>

        {/* Page Stats Badge */}
        {hasPageData && (
          <div className="hidden group-hover:flex items-center gap-1.5 flex-shrink-0">
            {node.pageData!.forms_count > 0 && (
              <div className="flex items-center gap-0.5 text-[9px] text-accent-purple">
                <FormInput className="w-2.5 h-2.5" />
                <span>{node.pageData!.forms_count}</span>
              </div>
            )}
            {node.pageData!.buttons_count > 0 && (
              <div className="flex items-center gap-0.5 text-[9px] text-accent-cyan">
                <MousePointerClick className="w-2.5 h-2.5" />
                <span>{node.pageData!.buttons_count}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Children */}
      {isExpanded && hasChildren && (
        <div className="relative">
          {/* Vertical line */}
          <div
            className="absolute left-0 top-0 bottom-0 w-px bg-border"
            style={{ left: `${level * 10 + 12}px` }}
          />
          {node.children.map((child) => (
            <TreeNodeItem key={child.path} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}
