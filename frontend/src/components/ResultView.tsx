import type { AnalysisResult } from "../types/analysis";
import RiskGauge from "./RiskGauge";
import { riskBgClass, formatCategory } from "../lib/risk";
import { ShieldAlert, ShieldCheck, Link2, FileText, Sparkles, AlertTriangle } from "lucide-react";

export default function ResultView({ result }: { result: AnalysisResult }) {
  const isSafe = result.risk_level === "Low";

  return (
    <div className="space-y-6">
      {/* Header risk card */}
      <div className={`rounded-2xl border p-6 flex flex-col md:flex-row items-center gap-6 ${riskBgClass(result.risk_level)}`}>
        <RiskGauge score={result.overall_risk_score} level={result.risk_level} />
        <div className="flex-1 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
            {isSafe ? <ShieldCheck size={28} /> : <ShieldAlert size={28} />}
            <h2 className="text-2xl font-bold tracking-tight">
              {result.risk_level.toUpperCase()} RISK
            </h2>
          </div>
          <p className="text-sm opacity-80 mb-1">
            Type: <span className="font-semibold">{formatCategory(result.scam_category)}</span>
          </p>
          <p className="text-sm opacity-80">
            Confidence: <span className="font-semibold">{result.confidence}%</span>
          </p>
          <div className="flex gap-3 mt-3 justify-center md:justify-start flex-wrap">
            {Object.entries(result.signals).map(([key, val]) => (
              <span key={key} className="text-xs bg-black/20 rounded-full px-3 py-1 border border-white/10">
                {key === "text" ? "Text Risk" : "URL Risk"}: {Math.round(val)}%
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Evidence */}
      <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-6">
        <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
          <AlertTriangle size={20} className="text-amber-400" /> Why this was flagged
        </h3>
        <ul className="space-y-2">
          {result.evidence.map((e, i) => (
            <li key={i} className="text-sm text-slate-300 flex gap-2">
              <span className="text-amber-400 mt-0.5">•</span> {e}
            </li>
          ))}
        </ul>
      </div>

      {/* AI Investigation */}
      <div className="rounded-2xl border border-indigo-700/40 bg-indigo-950/30 p-6">
        <h3 className="font-semibold text-lg mb-3 flex items-center gap-2 text-indigo-300">
          <Sparkles size={20} /> AI Investigator
          {result.ai_investigation.generated_by !== "llm" && (
            <span className="text-[10px] uppercase tracking-wide bg-indigo-800/60 px-2 py-0.5 rounded-full text-indigo-200">
              rule-based (no LLM key configured)
            </span>
          )}
        </h3>
        <p className="text-sm text-slate-200 mb-4">{result.ai_investigation.simple_explanation}</p>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">What the attacker wants</p>
            <p className="text-sm text-slate-300">{result.ai_investigation.attacker_goal}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">Recommended action</p>
            <ul className="space-y-1">
              {result.ai_investigation.recommended_action.map((a, i) => (
                <li key={i} className="text-sm text-green-300 flex gap-2">
                  <span>✓</span> {a}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Detail panels */}
      <div className="grid md:grid-cols-2 gap-6">
        {result.text_analysis && (
          <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-6">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <FileText size={18} /> Text Analysis
            </h3>
            <p className="text-sm text-slate-400 mb-1">
              Scam probability: <span className="text-slate-200 font-medium">{result.text_analysis.scam_probability}%</span>
            </p>
            {result.text_analysis.scam_type && (
              <p className="text-sm text-slate-400 mb-3">
                Detected type: <span className="text-slate-200 font-medium">{formatCategory(result.text_analysis.scam_type)}</span>
              </p>
            )}
            {result.text_analysis.top_terms.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {result.text_analysis.top_terms.map((t, i) => (
                  <span key={i} className="text-xs bg-slate-800 border border-slate-700 rounded-full px-2 py-1">
                    {t.term}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {result.url_analysis && (
          <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-6">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Link2 size={18} /> URL Analysis
            </h3>
            <p className="text-sm text-slate-400 mb-1 break-all">{result.url_analysis.url}</p>
            <p className="text-sm text-slate-400 mb-1">
              Malicious probability:{" "}
              <span className="text-slate-200 font-medium">{result.url_analysis.malicious_probability}%</span>
            </p>
            <div className="flex gap-2 flex-wrap mt-2">
              {!result.url_analysis.features.is_https && (
                <span className="text-xs bg-red-900/40 text-red-300 rounded-full px-2 py-1">No HTTPS</span>
              )}
              {result.url_analysis.features.suspicious_tld && (
                <span className="text-xs bg-red-900/40 text-red-300 rounded-full px-2 py-1">Suspicious TLD</span>
              )}
              {result.url_analysis.features.possible_brand_impersonation && (
                <span className="text-xs bg-red-900/40 text-red-300 rounded-full px-2 py-1">Brand impersonation</span>
              )}
              {result.url_analysis.features.has_url_shortener && (
                <span className="text-xs bg-red-900/40 text-red-300 rounded-full px-2 py-1">Shortened link</span>
              )}
            </div>
          </div>
        )}

        {result.ocr && (
          <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-6 md:col-span-2">
            <h3 className="font-semibold mb-3">OCR Extracted Text</h3>
            <p className="text-xs text-slate-500 mb-2">Confidence: {result.ocr.ocr_confidence}%</p>
            <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans bg-slate-950/60 rounded-lg p-3 border border-slate-800">
              {result.ocr.extracted_text}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
