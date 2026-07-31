import { Link } from "react-router-dom";
import {
  AssetCriticalityBadge,
  AssetEnvironmentBadge,
  AssetStatusBadge,
  AssetTypeBadge,
} from "./AssetBadges";
import { getPrimaryMetadataValue } from "../types";
import { UNAVAILABLE } from "../utils";

export default function AssetTable({ assets, projectId, projectName }) {
  if (assets.length === 0) {
    return (
      <div className="glass-panel p-8 text-center">
        <p className="text-brand-400">No assets match your filters.</p>
      </div>
    );
  }

  return (
    <div className="glass-panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-brand-800/50 bg-brand-950/30 text-xs uppercase tracking-wide text-brand-500">
            <tr>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Project</th>
              <th className="px-4 py-3 font-medium">Criticality</th>
              <th className="px-4 py-3 font-medium">Environment</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Owner</th>
              <th className="px-4 py-3 font-medium">Last Scan</th>
              <th className="px-4 py-3 font-medium">Risk Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-800/40">
            {assets.map((asset) => {
              const primary = getPrimaryMetadataValue(asset);
              return (
                <tr key={asset.id} className="hover:bg-brand-900/20">
                  <td className="px-4 py-3">
                    <AssetTypeBadge type={asset.type} />
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/projects/${projectId}/assets/${asset.id}`}
                      className="link-glow font-medium text-brand-100"
                    >
                      {asset.name}
                    </Link>
                    {primary && (
                      <p className="mt-0.5 text-xs text-brand-500">{primary}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-brand-300">{projectName ?? "—"}</td>
                  <td className="px-4 py-3">
                    <AssetCriticalityBadge criticality={asset.criticality} />
                  </td>
                  <td className="px-4 py-3">
                    <AssetEnvironmentBadge environment={asset.environment} />
                  </td>
                  <td className="px-4 py-3">
                    <AssetStatusBadge status={asset.status} />
                  </td>
                  <td className="px-4 py-3 text-brand-300">{asset.owner || "—"}</td>
                  <td className="px-4 py-3 text-brand-500">{UNAVAILABLE}</td>
                  <td className="px-4 py-3 text-brand-500">{UNAVAILABLE}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
