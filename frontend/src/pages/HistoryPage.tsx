import { useEffect, useState } from "react";
import { getHistory, deleteEntry, clearHistory } from "../lib/storage";
import type { HistoryEntry } from "../types/analysis";
import ResultView from "../components/ResultView";
import { riskBgClass, formatCategory } from "../lib/risk";
import { History as HistoryIcon, Trash2, X } from "lucide-react";

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [selected, setSelected] = useState<HistoryEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadHistory() {
    try {
      setError("");
      setLoading(true);

      const history = await getHistory();
      setEntries(history);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();

    try {
      setError("");

      await deleteEntry(id);

      setEntries((current) => current.filter((entry) => entry.id !== id));

      if (selected?.id === id) {
        setSelected(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete analysis.");
    }
  }

  async function handleClearAll() {
    if (!confirm("Clear all analysis history? This cannot be undone.")) {
      return;
    }

    try {
      setError("");

      await clearHistory();

      setEntries([]);
      setSelected(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to clear history.");
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <HistoryIcon className="text-indigo-400" size={32} />

          <div>
            <h1 className="text-2xl font-bold">Analysis History</h1>

            <p className="text-slate-400 text-sm">
              Your previously analyzed messages, URLs, and screenshots.
            </p>
          </div>
        </div>

        {entries.length > 0 && (
          <button
            onClick={handleClearAll}
            className="text-xs text-red-400 border border-red-900 hover:bg-red-950/40 rounded-lg px-3 py-2 flex items-center gap-1"
          >
            <Trash2 size={14} /> Clear all
          </button>
        )}
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center text-slate-400">
          Loading your analysis history...
        </div>
      ) : entries.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center text-slate-400">
          No analysis history yet.
        </div>
      ) : (
        <div className="space-y-3">
          {entries.map((entry) => (
            <div
              key={entry.id}
              onClick={() => setSelected(entry)}
              className={`rounded-xl border p-4 flex items-center justify-between gap-4 cursor-pointer hover:brightness-110 transition ${riskBgClass(
                entry.risk_level
              )}`}
            >
              <div className="min-w-0">
                <p className="text-sm font-medium truncate max-w-lg">
                  {entry.input_summary}
                </p>

                <p className="text-xs opacity-70">
                  {entry.input_type.toUpperCase()} ·{" "}
                  {formatCategory(entry.scam_category)} ·{" "}
                  {new Date(entry.timestamp).toLocaleString()}
                </p>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <span className="text-sm font-bold">
                  {Math.round(entry.overall_risk_score)}/100
                </span>

                <button
                  onClick={(e) => handleDelete(entry.id, e)}
                  className="text-slate-400 hover:text-red-400"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selected && (
        <div
          className="fixed inset-0 bg-black/70 z-50 flex items-start justify-center overflow-y-auto p-4"
          onClick={() => setSelected(null)}
        >
          <div
            className="bg-slate-950 border border-slate-800 rounded-2xl max-w-4xl w-full my-8 p-6 relative"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelected(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X size={22} />
            </button>

            <ResultView result={selected} />
          </div>
        </div>
      )}
    </div>
  );
}