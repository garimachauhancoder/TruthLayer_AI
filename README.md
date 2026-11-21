# TruthLayer AI 🔍
### AI-Powered Document Fact-Checking & Evidence Verification System

TruthLayer AI is an intelligent fact-checking application that analyzes PDF documents, extracts verifiable factual claims, and evaluates their accuracy using real-time web evidence and Google's Gemini AI.

The application helps users identify potentially inaccurate information, validate factual statements, and understand the evidence behind each verdict through an interactive dashboard.

---

## 🚀 Key Features

- **Multi-PDF Processing:** Upload and audit multiple PDF documents in one run, then switch between document-specific results, highlighted PDFs, and reports.
- **AI-Powered Claim Extraction:** Uses Google Gemini to identify checkable claims, including statistics, dates, financial figures, and technical information. Each result retains the exact original sentence and its validated PDF page number alongside the concise claim used for checking.
- **Real-Time Evidence Search:** Uses Tavily Search API to retrieve relevant web evidence for individual claims.
- **Interactive Web Search:** The search field at the top runs live searches across general web results and recent news, showing source links, excerpts, search topic, and publication dates when available.
- **Two-Sided Search and Publication Dates:** Searches each claim for both supporting and contradicting evidence, and displays the publication date returned by Tavily when available. Missing dates are identified as unavailable.
- **Automated Fact Verification:** Evaluates retrieved evidence using Gemini and generates an appropriate verdict.
- **Source Attribution:** Displays supporting source links and original PDF page references.
- **Problematic Claim Highlighting:** Adds red PDF annotations to claims marked False and amber annotations to claims marked Inaccurate. The app previews affected pages, identifies claim numbers and page numbers, and provides a downloadable annotated PDF.
- **Interactive Analytics Dashboard:** Presents verification statistics, verdict distribution, charts, and an overall factuality score.
- **PDF and CSV Report Export:** Lets users choose a report format with original claims, verdicts, corrections, explanations, evidence excerpts, and source URLs.
- **Built-in Sample Document:** Includes a sample PDF so users can test the application without uploading their own document.

---

## ⚙️ How It Works

TruthLayer AI follows a multi-stage verification pipeline:

1. **Document Upload:** The user uploads one or more text-based PDFs or selects the built-in sample document.
2. **Text Extraction:** PyMuPDF extracts the document's text while preserving page-level information.
3. **Claim Identification:** Gemini identifies factual statements that can be independently verified. The document is processed in page-labeled chunks, and each returned verbatim sentence is matched against the extracted PDF text to validate or correct its page number.
4. **Evidence Retrieval:** Tavily searches from supporting and contradicting angles for each extracted claim, adds news search results when general results lack publication dates, and retains result URLs, excerpts, search angle, topic, and dates when the API provides them.
5. **AI Verification:** Gemini evaluates the retrieved evidence and determines the accuracy of each claim.
6. **Results & Reporting:** Choose an audited PDF to view its claims, analytics, highlights, and sources. Download its fact-check report as PDF or CSV, or download a separate annotated PDF. Reports include claims, verdicts, corrections, explanations, evidence excerpts, and source URLs; analytics remain in the dashboard.

### System Workflow

```text
       PDF Document
             |
             ▼
      Text Extraction
        (PyMuPDF)
             |
             ▼
     AI Claim Extraction
         (Gemini)
             |
             ▼
      Web Evidence Search
         (Tavily)
             |
             ▼
      Evidence Evaluation
         (Gemini)
             |
             ▼
      Verification Results
             |
       ┌─────┴─────┐
       ▼           ▼
   Dashboard    PDF / CSV Reports
                Highlighted PDF
```

---

## 📊 Verification Categories

Each extracted claim is assigned one of four verification verdicts:

| Verdict | Description |
|---|---|
| Verified | Available evidence supports the claim. |
| Inaccurate | The claim contains incorrect or misleading details. |
| False | Available evidence contradicts the claim. |
| Insufficient Evidence | Available evidence is insufficient to reach a reliable conclusion. |

**Important:** Lack of supporting evidence does not automatically mean a claim is false. TruthLayer AI uses the Insufficient Evidence category when the available information is inconclusive.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| Streamlit | Interactive web interface and dashboard |
| Google Gemini AI | Claim extraction and evidence evaluation |
| Tavily API | Real-time web search and evidence retrieval |
| PyMuPDF | PDF text extraction, annotation, preview, and report generation |
| Pandas | Result processing and CSV export |
| Plotly | Interactive charts and visual analytics |

---

## 📁 Project Structure

```text
factcheck-agent/
│
├── .streamlit/
│   └── config.toml
│
├── app.py                 # Main Streamlit application
├── ai_client.py           # Gemini and Vertex AI configuration
├── claim_extractor.py     # Factual claim extraction
├── fact_checker.py        # Evidence assessment and verdicts
├── factcheck.py           # Fact-checking utilities
├── pdf_processor.py       # PDF text extraction
├── pdf_highlighter.py     # In-PDF claim highlighting and page previews
├── report_generator.py    # Paginated PDF fact-check report generation
├── web_search.py          # Tavily web search integration
│
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Git ignored files
└── README.md              # Project documentation
```

---

## 💻 Installation & Setup

### Prerequisites

- Python 3.10 or newer
- Google Gemini API Key
- Tavily API Key
- Internet connection

### 1. Clone the Repository

```bash
git clone https://github.com/garimachauhancoder/Fact_Checking_Web_App.git
```

### 2. Navigate to the Project Directory

```bash
cd Fact_Checking_Web_App
```

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

### 4. Activate the Virtual Environment

**For Windows (Git Bash):**

```bash
source .venv/Scripts/activate
```

**For Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure API Keys

Create a `.env` file in the project root directory using `.env.example` as a template.

Add your API credentials:

```env
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Alternatively, configure the credentials through Streamlit secrets.

**Note:** Never commit your actual API keys or `.env` file to GitHub.

### 7. Run the Application

```bash
streamlit run app.py
```

---

## 🔧 Configuration

TruthLayer AI supports the following optional configurations:

| Variable | Description | Default |
|---|---|---|
| GEMINI_MODEL | Specifies the Gemini model | gemini-2.5-flash |
| VERTEX_LOCATION | Vertex AI deployment location | us-central1 |
| GOOGLE_API_KEY | Alternative Gemini API key variable | Not set |

The application uses the Gemini API when a Gemini API key is configured. If that request fails, it tries Vertex AI when service account credentials are available.

A Gemini API key and Tavily API key are still required to enable document auditing through the application interface.

---

## 📄 Document Limitations

- Supports text-based PDF documents.
- Scanned or image-only PDFs without extractable text are not currently supported.
- Verification quality depends on the relevance, availability, and reliability of retrieved web evidence.
- AI-generated verdicts should be treated as decision-support information and independently reviewed for critical use cases.

---

## 🎯 Project Objective

The objective of TruthLayer AI is to simplify document-level fact verification by combining artificial intelligence, automated claim extraction, and real-time web evidence retrieval.

By bringing these capabilities together in a single application, the system helps users examine factual statements, identify inconsistencies, and make more informed decisions based on available evidence.

---

## 👩‍💻 Author

**Developed as an AI-powered fact-checking project.**

GitHub: [garimachauhancoder](https://github.com/garimachauhancoder)

---

⭐ If you find this project interesting, consider giving the repository a star!
