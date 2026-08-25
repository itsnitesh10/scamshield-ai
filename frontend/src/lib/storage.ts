import { supabase } from "./supabase";
import type { AnalysisResult, HistoryEntry } from "../types/analysis";

type AnalysisRow = {
  id: string;
  user_id: string;
  input_type: HistoryEntry["input_type"];
  input_summary: string;
  overall_risk_score: number;
  risk_level: HistoryEntry["risk_level"];
  scam_category: string | null;
  confidence: number;
  evidence: string[];
  signals: Record<string, number>;
  text_analysis: AnalysisResult["text_analysis"];
  url_analysis: AnalysisResult["url_analysis"];
  ocr: AnalysisResult["ocr"];
  ai_investigation: AnalysisResult["ai_investigation"];
  created_at: string;
};

function rowToHistoryEntry(row: AnalysisRow): HistoryEntry {
  return {
    id: row.id,
    timestamp: row.created_at,
    input_summary: row.input_summary,
    input_type: row.input_type,
    overall_risk_score: row.overall_risk_score,
    risk_level: row.risk_level,
    scam_category: row.scam_category,
    confidence: row.confidence,
    evidence: row.evidence ?? [],
    signals: row.signals ?? {},
    text_analysis: row.text_analysis ?? null,
    url_analysis: row.url_analysis ?? null,
    ocr: row.ocr ?? null,
    ai_investigation: row.ai_investigation,
  };
}

export async function getHistory(): Promise<HistoryEntry[]> {
  const { data, error } = await supabase
    .from("analyses")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) {
    throw new Error(error.message);
  }

  return (data ?? []).map((row) => rowToHistoryEntry(row as AnalysisRow));
}

export async function saveEntry(
  result: AnalysisResult,
  inputType: HistoryEntry["input_type"],
  inputSummary: string
): Promise<HistoryEntry> {
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    throw new Error("You must be logged in to save an analysis.");
  }

  const { data, error } = await supabase
    .from("analyses")
    .insert({
      user_id: user.id,
      input_type: inputType,
      input_summary: inputSummary.slice(0, 160),
      overall_risk_score: result.overall_risk_score,
      risk_level: result.risk_level,
      scam_category: result.scam_category,
      confidence: result.confidence,
      evidence: result.evidence,
      signals: result.signals,
      text_analysis: result.text_analysis,
      url_analysis: result.url_analysis,
      ocr: result.ocr,
      ai_investigation: result.ai_investigation,
    })
    .select()
    .single();

  if (error) {
    throw new Error(error.message);
  }

  return rowToHistoryEntry(data as AnalysisRow);
}

export async function deleteEntry(id: string): Promise<void> {
  const { error } = await supabase
    .from("analyses")
    .delete()
    .eq("id", id);

  if (error) {
    throw new Error(error.message);
  }
}

export async function clearHistory(): Promise<void> {
  const { error } = await supabase
    .from("analyses")
    .delete()
    .neq("id", "");

  if (error) {
    throw new Error(error.message);
  }
}

export async function getStats() {
  const all = await getHistory();

  const total = all.length;

  const scams = all.filter(
    (e) => e.scam_category || e.risk_level !== "Low"
  ).length;

  const highRisk = all.filter(
    (e) => e.risk_level === "High" || e.risk_level === "Critical"
  ).length;

  const categoryCounts: Record<string, number> = {};

  all.forEach((e) => {
    if (e.scam_category) {
      categoryCounts[e.scam_category] =
        (categoryCounts[e.scam_category] || 0) + 1;
    }
  });

  const riskDistribution = {
    Low: 0,
    Medium: 0,
    High: 0,
    Critical: 0,
  };

  all.forEach((e) => {
    riskDistribution[e.risk_level] =
      (riskDistribution[e.risk_level] || 0) + 1;
  });

  return {
    total,
    scams,
    highRisk,
    categoryCounts,
    riskDistribution,
    recent: all.slice(0, 5),
  };
}