#  ScamShield AI

### Multimodal Scam Detection & Risk Analysis Platform

 **Live Demo:** https://scamshield-ai-1-qjfr.onrender.com

 **GitHub:** https://github.com/itsnitesh10/scamshield-ai

ScamShield AI is a multimodal scam-detection platform that analyzes **suspicious text, URLs, and screenshots** and provides an ML-driven risk assessment with detected signals and recommended actions.

> The live demo may take a few seconds to respond if the backend has been idle on Render's free tier.

---

##  How It Works

```text
User Input
   ↓
Text / URL / Screenshot
   ↓
ML / URL Analysis / OCR
   ↓
Risk Engine
   ↓
Risk Score + Category + Evidence
   ↓
Result & Recommended Action
 Text Analysis

Uses TF-IDF + Machine Learning to detect suspicious text and classify scam types.

 URL Analysis

Extracts structural URL features and uses a dedicated ML model to identify suspicious URLs without automatically opening them.

 Screenshot Analysis

Uses Tesseract OCR to extract text from screenshots and sends the extracted content through the text-analysis pipeline.

 Risk Engine

Combines available detection signals into a structured risk assessment including:

Risk score
Risk level
Scam category
Confidence
Detected signals
Recommended action
 AI Investigator

ScamShield includes an AI Investigator layer designed to turn structured detection evidence into understandable explanations and recommendations.

The architecture supports optional LLM providers, while the current deployed version can operate without an external LLM provider using deterministic explanations.

 Architecture
                    ScamShield AI
                          │
          ┌───────────────┼───────────────┐
          ↓               ↓               ↓
        TEXT          SCREENSHOT          URL
          │               │               │
          │              OCR          URL Features
          │               ↓               │
          └───────────────┼───────────────┘
                          ↓
                    ML Inference
                          ↓
                     Risk Engine
                          ↓
              Risk + Evidence + Action
                          ↓
                    React Frontend
 Tech Stack

Frontend

React
TypeScript
Vite
Tailwind CSS
Recharts

Backend

Python
FastAPI
Uvicorn

AI / ML

Scikit-learn
TF-IDF
Tesseract OCR
joblib

Platform

Supabase Authentication
PostgreSQL
Docker
Render
 Security
Suspicious URLs are analyzed structurally rather than automatically opened.
API requests and uploaded files are validated.
Rate limiting is included in the backend.
Secrets and private credentials are kept outside the source code.
Supabase Row Level Security policies are included for persistent user data.
 Project Structure
scamshield-ai/
├── backend/
│   ├── app/
│   │   ├── ml/
│   │   ├── url_analysis/
│   │   ├── ocr/
│   │   ├── risk_engine/
│   │   ├── ai_investigator/
│   │   ├── api/
│   │   └── core/
│   ├── models/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── lib/
│       └── types/
│
├── supabase/
│   └── schema.sql
│
└── README.md
 Run Locally
Backend
cd backend
python -m venv venv

Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Run:

uvicorn app.main:app --reload --port 8000

API documentation:

http://localhost:8000/docs
Frontend
cd frontend
npm install
npm run dev
 Limitations
The included ML training dataset is synthetic/template-based and is not a large real-world scam dataset.
ML predictions can produce false positives and false negatives.
OCR accuracy depends on screenshot quality.
The current rate limiter is process-local.
The deployed version currently does not use an external LLM provider.

For production-scale deployment, the models should be retrained and evaluated using larger, diverse real-world datasets.

 Future Improvements
Larger real-world training datasets
Transformer-based NLP models
Persistent Supabase-backed analysis history
Semantic similarity and embeddings
Similar-scam search
Background processing for expensive OCR/ML workloads
Redis-backed rate limiting
Horizontal backend scaling
 Author

Nitesh Bhoir

 GitHub: https://github.com/itsnitesh10

 Try ScamShield AI

Live Demo:
https://scamshield-ai-1-qjfr.onrender.com

If you find an issue or have feedback, feel free to open an issue or reach out.
