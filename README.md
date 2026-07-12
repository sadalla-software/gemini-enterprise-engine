# 🚀 Gemini Enterprise Engine (GEE)

**AI-powered bookkeeping and financial advisory for African SMEs — speak or type a transaction in Swahili or English, and let Gemini handle the accounting.**

> Built for the [Build with Gemini XPRIZE](https://xprize.devpost.com/) — a $2M global hackathon backed by XPRIZE and Google, challenging builders to ship real AI-native businesses in 90 days.

---

## 💡 The Problem

Most small business owners in Africa don't have time — or formal training — to keep structured financial records. Transactions get scribbled in notebooks or simply forgotten, which makes it nearly impossible to know if the business is actually profitable, and even harder to produce the financial statements banks require for loans.

## ✅ The Solution

**Gemini Enterprise Engine** turns a spoken or typed sentence like *"Nauzia mkate faida ya shilingi elfu tano"* into a fully structured accounting record — automatically, in seconds.

### Key Features

- 🎙️ **Voice or text input** — record a transaction by voice (Swahili or English) or type it, no forms to fill
- 🤖 **AI-powered extraction** — Google Gemini (`gemini-2.5-flash`) parses natural language into structured JSON: transaction type (income/expense), exact amount, and description
- 📊 **Live business dashboard** — real-time income, expenses, and net profit, visualized with interactive Plotly charts
- 🧠 **AI Business Advisor** — Gemini analyzes the full transaction history and generates personalized, actionable strategic advice for the specific business, in Swahili
- 📄 **Bank-ready PDF reports** — one-click generation of a professional, certified financial statement (via ReportLab) that businesses can present to banks or investors
- 🗄️ **Cloud-synced records** — every transaction is persisted to Supabase (PostgreSQL), tied to the business profile

---

## 🏗️ Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│   Streamlit Frontend │ ──────▶ │   Gemini API           │
│   (app.py)            │         │   (gemini-2.5-flash)   │
│   - Voice/text input  │ ◀────── │   Structured JSON      │
│   - Dashboard          │        │   extraction            │
│   - AI Advisor         │        └──────────────────────┘
│   - PDF export          │
└──────────┬────────────┘
           │
           ▼
┌─────────────────────┐
│   Supabase (Postgres) │
│   transactions table  │
└─────────────────────┘

┌─────────────────────┐
│  FastAPI Service      │  ← standalone API layer for
│  (main.py)             │    future integrations
│  /api/process-transaction
└─────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| AI | Google Gemini API (`gemini-2.5-flash`) |
| Backend API | FastAPI + Pydantic |
| Database | Supabase (PostgreSQL) |
| Data & Viz | pandas, Plotly Express |
| Voice Input | streamlit-mic-recorder |
| Reporting | ReportLab (PDF generation) |

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/sadalla-software/gemini-enterprise-engine.git
cd gemini-enterprise-engine
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure secrets
Create a `.streamlit/secrets.toml` file (for the Streamlit app):
```toml
SUPABASE_KEY = "your-supabase-anon-key"
GEMINI_TOKEN = "your-gemini-api-key"
```

For the FastAPI service (`main.py`), create a `.env` file:
```
SUPABASE_URL=your-supabase-project-url
SUPABASE_KEY=your-supabase-anon-key
```

### 4. Run the app
```bash
streamlit run app.py
```

Or run the FastAPI backend:
```bash
python main.py
```

---

## 🎯 Category

Built for the **Small Business Services** / **Money & Financial Access** tracks of the Build with Gemini XPRIZE — helping underserved SME owners access proper financial record-keeping and, by extension, financial services like bank loans.

## 👤 Author

**Elisha Sadallah Kamwela** — Sadallah Software
📧 elishasadallah38@gmail.com

---

*This project is a work in progress, submitted as part of the Build with Gemini XPRIZE Hackathon 2026.*
