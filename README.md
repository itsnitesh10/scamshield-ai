# ScamShield AI

A multimodal scam-detection platform: paste text, a URL, or upload a screenshot,
and get a real ML-driven risk score, evidence, and an AI-generated explanation
and recommended action.

**Pipeline:** Input → ML Detection → Risk Score → Evidence → AI Explanation → Recommendation

This delivery covers **Phase 1–4** of the original spec end-to-end, built solid
and modular:

- Phase 1: Text/SMS ML classification + scam type + risk score
- Phase 2: URL/phishing detection
- Phase 3: Screenshot upload + OCR + text pipeline reuse
- Phase 4: AI Investigator (explanation + recommendation)

Phase 5 (auth + Supabase-backed history/dashboard) and Phase 6 (embeddings/
similar-scam search) are **not implemented as working features in this
delivery** — the frontend currently uses browser localStorage for history/
dashboard so those screens are fully functional standalone, and a complete,
ready-to-run Supabase SQL schema (`supabase/schema.sql`) is included for when
you're ready to wire in real auth-backed storage. See "Next steps" below.

---

## Project structure

```
scamshield-ai/
├── backend/                 # FastAPI + ML/NLP/OCR/URL analysis
│   ├── app/
│   │   ├── ml/               # text model training + inference
│   │   ├── url_analysis/     # URL feature extraction, training + inference
│   │   ├── ocr/               # Tesseract-based screenshot text extraction
│   │   ├── risk_engine/      # multimodal risk-score combiner
│   │   ├── ai_investigator/  # provider-agnostic LLM adapter + investigation logic
│   │   ├── api/               # FastAPI routes
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── core/               # config + rate limiting
│   │   └── data/               # training dataset generator
│   ├── models/                # trained .joblib model files (pre-trained, included)
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # React + TypeScript + Tailwind + Recharts
│   ├── src/
│   │   ├── pages/             # Analyze / Dashboard / History
│   │   ├── components/        # RiskGauge, ResultView
│   │   ├── lib/                # API client, risk display helpers, local history store
│   │   └── types/
│   └── .env.example
└── supabase/
    └── schema.sql             # Full DB schema + RLS policies for Phase 5
```

---

## Running it locally

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**System dependency:** OCR requires the Tesseract binary installed on your machine.
- macOS: `brew install tesseract`
- Ubuntu/Debian: `sudo apt install tesseract-ocr`
- Windows: install from https://github.com/UB-Mannheim/tesseract/wiki

**Windows note:** the Tesseract installer usually does not add itself to
your PATH, so pytesseract can't find it by default. In `backend/.env`, set:

```
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

adjusted to wherever you actually installed it (check for `tesseract.exe`
inside your Tesseract-OCR install folder). If `TESSERACT_CMD` is left blank,
the backend falls back to checking your system PATH — that's normally fine
on macOS/Linux, but usually needs setting explicitly on Windows. If neither
is found, the app now returns a clear error telling you what to fix instead
of a generic "not installed" message.

The text and URL ML models are **already trained and included** under
`backend/models/*.joblib`. To retrain them (e.g. after editing the dataset):

```bash
python -m app.data.build_dataset      # regenerate labeled_dataset.csv
python -m app.ml.train_text_model     # retrain text scam/type classifiers
python -m app.ml.train_url_model      # retrain URL malicious-link classifier
```

**If you see an error like `'LogisticRegression' object has no attribute 'multi_class'`:**
this means the saved `.joblib` model files were trained with a different
scikit-learn version than the one now installed on your machine. This is a
pickle-compatibility issue, not a code bug — fix it by simply retraining
locally with whatever scikit-learn version `pip install -r requirements.txt`
gave you:

```bash
python -m app.ml.train_text_model
```

This regenerates the model files against your exact local environment. You
only need to do this once after a fresh install (or after upgrading
scikit-learn).

To sanity-check the model on realistic examples it wasn't trained on
(distinct from the automated train/val/test split), run:

```bash
python -m app.ml.manual_eval
```


Copy the env file and configure it:

```bash
cp .env.example .env
```

Then run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs, or
`http://localhost:8000/api/health` for a quick check.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Visit `http://localhost:5173`.

For a production build: `npm run build` (outputs to `frontend/dist`), which
can be deployed to Vercel or any static host — just set `VITE_API_URL` to
your deployed backend URL.

---

## Configuring the AI Investigator (optional but recommended)

The AI Investigator works out of the box with **no API key** — it falls back
to a clear, deterministic rule-based explanation generator so the whole
pipeline (including the UI) is fully functional immediately.

To enable real LLM-generated explanations, edit `backend/.env`:

```
LLM_PROVIDER=anthropic      # or "openai"
LLM_API_KEY=sk-...
LLM_MODEL=claude-sonnet-5   # optional, sensible defaults are used if omitted
```

The adapter layer (`backend/app/ai_investigator/providers.py`) is written so
adding another OpenAI-compatible provider only requires a new small class —
the investigation logic itself never changes.

---

## Wiring up Supabase (for Phase 5: auth + persistent history)

1. Create a project at https://supabase.com
2. In the SQL editor, run `supabase/schema.sql` — this creates the
   `profiles` and `analyses` tables, a private `scam-screenshots` storage
   bucket, and Row Level Security policies so users can only ever read/write
   their own data.
3. Fill in `backend/.env`:
   ```
   SUPABASE_URL=https://xxxx.supabase.co
   SUPABASE_ANON_KEY=...
   SUPABASE_SERVICE_ROLE_KEY=...
   ```
4. The frontend's `src/lib/storage.ts` currently reads/writes browser
   localStorage. Its function signatures (`getHistory`, `saveEntry`,
   `deleteEntry`, `getStats`) were deliberately written to mirror what a
   Supabase-backed version looks like, so swapping the implementation to
   call `supabase-js` (with the user's session token) is a contained change
   that doesn't require touching any page or component.

This wasn't wired into working auth/login screens in this delivery to keep
the shipped project actually complete and tested end-to-end rather than
partially-stubbed; the schema and integration point are ready to go whenever
you want that phase built out.

---

## Known limitations (be aware of these)

- **ML training data** is a modular, labeled synthetic/template dataset
  (`backend/app/data/build_dataset.py`), not real-world scam data at scale.
  It generalizes reasonably to common phrasing patterns across all 12 scam
  categories, but a production deployment should retrain on a larger,
  real-world labeled dataset — the training pipeline accepts any CSV with
  `text,label,scam_type` columns, so this is a drop-in swap.
- **Rate limiting** is in-memory (per backend process), fine for a single
  instance; move to a Redis-backed limiter before horizontally scaling.
- **Phase 6 (embeddings/similar-scam search)** is not implemented.
- The bundled models score very well on held-out synthetic data (expected,
  since it's templated), which is not the same as real-world benchmark
  accuracy — treat current scores as "pipeline works correctly," not
  "production accuracy claim."
