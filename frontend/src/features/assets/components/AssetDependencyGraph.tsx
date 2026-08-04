import { Link } from "react-router-dom";
import type { AssetRelationshipGraph } from "@/shared/types/asset";
import { ASSET_TYPE_LABELS } from "../types";
import { AssetTypeBadge } from "./AssetBadges";

interface AssetDependencyGraphProps {
  graph: AssetRelationshipGraph;
  projectId: string;
}

export default function AssetDependencyGraph({ graph, projectId }: AssetDependencyGraphProps) {
  if (graph.nodes.length === 0) {
    return <p className="text-sm text-brand-500">No relationship graph available.</p>;
  }

  const nodesById = new Map(graph.nodes.map((node) => [node.id, node]));
  const parentEdges = graph.edges.filter((edge) => edge.kind === "parent");
  const linkEdges = graph.edges.filter((edge) => edge.kind === "link");

  const orderedNodes = [...graph.nodes].sort((a, b) => (a.depth ?? 0) - (b.depth ?? 0));

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-2">
        {orderedNodes.map((node, index) => (
          <div key={node.id} className="flex w-full max-w-md flex-col items-center">
            {index > 0 && parentEdges.some((edge) => edge.target === node.id) && (
              <div className="mb-2 flex h-8 flex-col items-center text-brand-600" aria-hidden>
                <span className="h-full w-px bg-brand-700/70" />
                <span className="text-xs">↓</span>
              </div>
            )}
            <Link
              to={`/projects/${projectId}/assets/${node.id}`}
              className={`w-full rounded-lg border px-4 py-3 transition-colors ${
                node.is_current
                  ? "border-brand-400/60 bg-brand-900/50 shadow-[0_0_24px_rgba(56,189,248,0.08)]"
                  : "border-brand-800/60 bg-brand-950/30 hover:border-brand-700/80 hover:bg-brand-900/30"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate font-medium text-brand-100">{node.name}</p>
                  {node.external_identifier && (
                    <p className="mt-0.5 truncate text-xs text-brand-500">
                      {node.external_identifier}
                    </p>
                  )}
                </div>
                <AssetTypeBadge type={node.type} />
              </div>
              {node.is_current && (
                <p className="mt-2 text-xs uppercase tracking-wide text-brand-400">Current asset</p>
              )}
            </Link>
          </div>
        ))}
      </div>

      {linkEdges.length > 0 && (
        <div>
          <p className="terminal-text mb-3 text-xs text-brand-500">linked connections</p>
          <ul className="space-y-2">
            {linkEdges.map((edge) => {
              const source = nodesById.get(edge.source);
              const target = nodesById.get(edge.target);
              if (!source || !target) return null;
              return (
                <li
                  key={`${edge.source}-${edge.target}-${edge.link_type}`}
                  className="rounded-lg border border-brand-800/50 px-3 py-2 text-sm text-brand-300"
                >
                  <span className="text-brand-100">{source.name}</span>
                  <span className="mx-2 text-brand-600">→</span>
                  <span className="text-brand-400">{edge.link_type?.replace("_", " ")}</span>
                  <span className="mx-2 text-brand-600">→</span>
                  <span className="text-brand-100">{target.name}</span>
                  {edge.label && <span className="ml-2 text-xs text-brand-500">({edge.label})</span>}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
