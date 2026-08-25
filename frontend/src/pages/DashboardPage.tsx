import { useEffect, useState } from "react";
import { getStats } from "../lib/storage";
import { riskBgClass, formatCategory } from "../lib/risk";
import { BarChart3, ShieldAlert, ShieldCheck, Layers } from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { Link } from "react-router-dom";

const RISK_COLORS: Record<string, string> = {
  Low: "#22c55e",
  Medium: "#eab308",
  High: "#f97316",
  Critical: "#ef4444",
};

type DashboardStats = Awaited<ReturnType<typeof getStats>>;

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadStats() {
    try {
      setError("");
      setLoading(true);

      const data = await getStats();
      setStats(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center text-slate-400">
          Loading your security dashboard...
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-red-300">
          {error || "Unable to load dashboard."}
        </div>
      </div>
    );
  }

  const riskData = Object.entries(stats.riskDistribution).map(
    ([name, value]) => ({
      name,
      value,
    })
  );

  const categoryData = Object.entries(stats.categoryCounts).map(
    ([name, value]) => ({
      name: formatCategory(name),
      value,
    })
  );

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-8">
        <BarChart3 className="text-indigo-400" size={32} />

        <div>
          <h1 className="text-2xl font-bold">Security Dashboard</h1>

          <p className="text-slate-400 text-sm">
            Overview of your scam analysis activity.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Layers size={20} />}
          label="Total Analyses"
          value={stats.total}
          color="text-indigo-400"
        />

        <StatCard
          icon={<ShieldAlert size={20} />}
          label="Scams Detected"
          value={stats.scams}
          color="text-orange-400"
        />

        <StatCard
          icon={<ShieldAlert size={20} />}
          label="High-Risk Detections"
          value={stats.highRisk}
          color="text-red-400"
        />

        <StatCard
          icon={<ShieldCheck size={20} />}
          label="Categories Found"
          value={Object.keys(stats.categoryCounts).length}
          color="text-green-400"
        />
      </div>

      {stats.total === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center text-slate-400">
          No analyses yet.{" "}
          <Link to="/" className="text-indigo-400 hover:underline">
            Run your first scan
          </Link>{" "}
          to see stats here.
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
            <h3 className="font-semibold mb-4">Risk Distribution</h3>

            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={riskData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                >
                  {riskData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={RISK_COLORS[entry.name]}
                    />
                  ))}
                </Pie>

                <Tooltip
                  contentStyle={{
                    background: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: 8,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>

            <div className="flex gap-4 justify-center flex-wrap mt-2 text-xs">
              {riskData.map((d) => (
                <span
                  key={d.name}
                  className="flex items-center gap-1"
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{
                      background: RISK_COLORS[d.name],
                    }}
                  />

                  {d.name} ({d.value})
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
            <h3 className="font-semibold mb-4">Scam Categories</h3>

            {categoryData.length === 0 ? (
              <p className="text-sm text-slate-500">
                No scams categorized yet.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart
                  data={categoryData}
                  layout="vertical"
                  margin={{ left: 20 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#1e293b"
                    horizontal={false}
                  />

                  <XAxis
                    type="number"
                    stroke="#64748b"
                    fontSize={11}
                  />

                  <YAxis
                    type="category"
                    dataKey="name"
                    stroke="#64748b"
                    fontSize={11}
                    width={120}
                  />

                  <Tooltip
                    contentStyle={{
                      background: "#0f172a",
                      border: "1px solid #334155",
                      borderRadius: 8,
                    }}
                  />

                  <Bar
                    dataKey="value"
                    fill="#6366f1"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}

      {stats.recent.length > 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <h3 className="font-semibold mb-4">Recent Analyses</h3>

          <div className="space-y-3">
            {stats.recent.map((r) => (
              <div
                key={r.id}
                className={`rounded-xl border p-4 flex items-center justify-between gap-4 ${riskBgClass(
                  r.risk_level
                )}`}
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate max-w-md">
                    {r.input_summary}
                  </p>

                  <p className="text-xs opacity-70">
                    {formatCategory(r.scam_category)} ·{" "}
                    {new Date(r.timestamp).toLocaleString()}
                  </p>
                </div>

                <span className="text-sm font-bold shrink-0">
                  {Math.round(r.overall_risk_score)}/100
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
      <div className={`mb-2 ${color}`}>{icon}</div>

      <p className="text-2xl font-bold">{value}</p>

      <p className="text-xs text-slate-400">{label}</p>
    </div>
  );
}