export interface TopTerm {
  term: string;
  contribution: number;
}

export interface TextAnalysis {
  scam_probability: number;
  predicted_label: "scam" | "safe";
  scam_type: string | null;
  scam_type_confidence: number | null;
  top_terms: TopTerm[];
}

export interface URLFeatures {
  url_length: number;
  domain_length: number;
  subdomain_count: number;
  is_https: boolean;
  suspicious_tld: boolean;
  suspicious_keyword_count: number;
  suspicious_keywords_found: string[];
  brand_mentioned: string[];
  possible_brand_impersonation: boolean;
  has_url_shortener: boolean;
  has_ip_address: boolean;
  domain_entropy: number;
  full_domain: string;
  [key: string]: any;
}

export interface URLAnalysis {
  url: string;
  malicious_probability: number;
  ml_probability: number | null;
  heuristic_probability: number;
  features: URLFeatures;
  evidence: string[];
}

export interface OCRResult {
  extracted_text: string;
  ocr_confidence: number;
  char_count: number;
  image_size: [number, number];
}

export interface AIInvestigation {
  simple_explanation: string;
  why_suspicious: string[];
  attacker_goal: string;
  recommended_action: string[];
  generated_by: string;
}

export interface AnalysisResult {
  overall_risk_score: number;
  risk_level: "Low" | "Medium" | "High" | "Critical";
  scam_category: string | null;
  confidence: number;
  evidence: string[];
  signals: Record<string, number>;
  text_analysis: TextAnalysis | null;
  url_analysis: URLAnalysis | null;
  ocr: OCRResult | null;
  ai_investigation: AIInvestigation;
}

export interface HistoryEntry extends AnalysisResult {
  id: string;
  timestamp: string;
  input_summary: string;
  input_type: "text" | "url" | "image" | "combined";
}
