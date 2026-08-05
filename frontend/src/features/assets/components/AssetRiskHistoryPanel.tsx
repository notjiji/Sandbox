import { useEffect, useState } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { AssetRiskHistory, RiskHistoryChange } from "@/shared/types/risk-history";
import { SectionPanel } from "@/features/organizations/components/dashboard/StatCard";
import { assetsApi } from "../api";
import AssetRiskHistoryChart, { RiskScoreTrail } from "./AssetRiskHistoryChart";

interface AssetRiskHistoryPanelProps {
  projectId: string;
  assetId: string;
}

function formatRiskDelta(delta: number): string {
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta.toFixed(0)}`;
}

function ChangeExplanationList({ change }: { change: RiskHistoryChange }) {
  if (change.explanations.length === 0) {
    return (
      <p className="text-sm text-brand-600">
        Score changed from {change.from_score.toFixed(0)} to {change.to_score.toFixed(0)}.
        No individual finding changes were recorded in this period.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {change.explanations.map((item) => (
        <li
          key={`${item.kind}-${item.finding_id ?? item.title}`}
          className="flex items-start gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3"
        >
          <span
            className={`shrink-0 font-mono text-sm font-semibold tabular-nums ${
              item.delta > 0 ? "text-red-300" : "text-emerald-300"
            }`}
          >
            {formatRiskDelta(item.delta)}
          </span>
          <div>
            <p className="text-sm text-brand-100">{item.title}</p>
            {item.severity && (
              <p className="text-xs capitalize text-brand-600">{item.severity}</p>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function AssetRiskHistoryPanel({ projectId, assetId }: AssetRiskHistoryPanelProps) {
  const [history, setHistory] = useState<AssetRiskHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedChangeIndex, setSelectedChangeIndex] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    assetsApi
      .riskHistory(projectId, assetId)
      .then((response) => {
        if (active) setHistory(response ?? null);
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof ApiError ? err.message : "Unable to load risk history.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [projectId, assetId]);

  const changes = history?.changes ?? [];
  const selectedChange = changes[selectedChangeIndex] ?? history?.latest_change ?? null;
  const trend = history?.trend ?? [];
  const latestDelta = trend.length > 1 ? trend[trend.length - 1]?.score_delta : null;

  return (
    <SectionPanel title="Risk history">
      {error && <FormAlert message={error} />}

      {loading ? (
        <p className="text-sm text-brand-600">Loading risk history...</p>
      ) : trend.length === 0 ? (
        <p className="text-sm text-brand-600">
          Complete multiple scans to build a risk score trend.
        </p>
      ) : (
        <div className="space-y-6">
          <div>
            <div className="mb-3 flex items-center gap-3">
              <RiskScoreTrail points={trend} />
              {latestDelta != null && latestDelta !== 0 && (
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs ${
                    latestDelta > 0
                      ? "bg-emerald-950/40 text-emerald-300"
                      : "bg-red-950/40 text-red-300"
                  }`}
                >
                  {latestDelta > 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  {latestDelta > 0 ? "+" : ""}
                  {latestDelta.toFixed(0)} latest
                </span>
              )}
            </div>
            <AssetRiskHistoryChart points={trend} />
          </div>

          {selectedChange && (
            <section>
              <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-brand-100">Why did it change?</h3>
                  <p className="text-xs text-brand-600">
                    {selectedChange.from_score.toFixed(0)} → {selectedChange.to_score.toFixed(0)}{" "}
                    ({selectedChange.score_delta > 0 ? "+" : ""}
                    {selectedChange.score_delta.toFixed(0)} score)
                  </p>
                </div>
                {changes.length > 1 && (
                  <select
                    value={selectedChangeIndex}
                    onChange={(e) => setSelectedChangeIndex(Number(e.target.value))}
                    className="input-field w-auto py-1.5 text-sm"
                    aria-label="Select risk change period"
                  >
                    {changes.map((change, index) => (
                      <option key={`${change.from_date}-${change.to_date}`} value={index}>
                        {new Date(change.to_date).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                        })}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              <ChangeExplanationList change={selectedChange} />
            </section>
          )}
        </div>
      )}
    </SectionPanel>
  );
}
