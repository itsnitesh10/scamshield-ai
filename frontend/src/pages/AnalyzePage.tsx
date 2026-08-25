import { useState, useRef } from "react";
import { analyzeText, analyzeURL, analyzeCombined, analyzeImage, APIError } from "../lib/api";
import { saveEntry } from "../lib/storage";
import ResultView from "../components/ResultView";
import type { AnalysisResult } from "../types/analysis";
import { MessageSquareText, Link2, ImageUp, Loader2, ShieldQuestion } from "lucide-react";

type Tab = "text" | "url" | "image";

export default function AnalyzePage() {
  const [tab, setTab] = useState<Tab>("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      let res: AnalysisResult;
      let summary = "";
      if (tab === "text") {
        if (!text.trim()) throw new Error("Please enter some text to analyze.");
        res = url.trim() ? await analyzeCombined(text, url) : await analyzeText(text);
        summary = text;
      } else if (tab === "url") {
        if (!url.trim()) throw new Error("Please enter a URL to analyze.");
        res = await analyzeURL(url);
        summary = url;
      } else {
        if (!file) throw new Error("Please choose an image to analyze.");
        res = await analyzeImage(file);
        summary = file.name;
      }
      	setResult(res);

	await saveEntry(res, tab, summary);
      
    } catch (e) {
      if (e instanceof APIError) setError(e.message);
      else if (e instanceof Error) setError(e.message);
      else setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "text", label: "Text / SMS / Chat", icon: <MessageSquareText size={16} /> },
    { id: "url", label: "URL", icon: <Link2 size={16} /> },
    { id: "image", label: "Screenshot", icon: <ImageUp size={16} /> },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <ShieldQuestion className="text-indigo-400" size={32} />
        <div>
          <h1 className="text-2xl font-bold">Analyze Content</h1>
          <p className="text-slate-400 text-sm">
            Paste a message, a link, or upload a screenshot to check for scams.
          </p>
        </div>
      </div>

      <div className="flex gap-2 mb-4 bg-slate-900/60 border border-slate-800 rounded-xl p-1 w-fit">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === t.id ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 mb-6">
        {tab === "text" && (
          <div className="space-y-3">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste the SMS, WhatsApp message, or email text here..."
              rows={6}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Optional: include a related URL mentioned in the message"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        )}

        {tab === "url" && (
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste a suspicious URL, e.g. http://example-verify.xyz"
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        )}

        {tab === "image" && (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-700 rounded-xl p-10 text-center cursor-pointer hover:border-indigo-500 transition"
          >
            <ImageUp className="mx-auto mb-3 text-slate-500" size={32} />
            <p className="text-sm text-slate-400">
              {file ? file.name : "Click to upload a WhatsApp/SMS/email/payment screenshot"}
            </p>
            <p className="text-xs text-slate-600 mt-1">JPG, PNG or WEBP, up to 8MB</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </div>
        )}

        {error && (
          <div className="mt-4 text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg p-3">
            {error}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="mt-4 w-full md:w-auto flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white font-medium px-6 py-3 rounded-xl transition"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={18} /> Analyzing...
            </>
          ) : (
            "Analyze"
          )}
        </button>
      </div>

      {result && <ResultView result={result} />}
    </div>
  );
}
