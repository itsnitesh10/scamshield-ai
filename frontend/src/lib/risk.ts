export function riskColor(level: string): string {
  switch (level) {
    case "Critical":
      return "#ef4444";
    case "High":
      return "#f97316";
    case "Medium":
      return "#eab308";
    default:
      return "#22c55e";
  }
}

export function riskBgClass(level: string): string {
  switch (level) {
    case "Critical":
      return "bg-red-500/10 border-red-500/40 text-red-400";
    case "High":
      return "bg-orange-500/10 border-orange-500/40 text-orange-400";
    case "Medium":
      return "bg-yellow-500/10 border-yellow-500/40 text-yellow-400";
    default:
      return "bg-green-500/10 border-green-500/40 text-green-400";
  }
}

export function formatCategory(cat: string | null): string {
  if (!cat) return "Uncategorized";
  return cat
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
