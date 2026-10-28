# 🌌 AI Expense Tracker with 3D Interactive Dashboard

An intelligent, full-stack financial operating system built with **Python 3.11**, **Streamlit**, **Three.js**, **Pandas**, **NumPy**, **Plotly**, **Matplotlib**, **SQLite**, and **Ollama**.

The application accepts expenses typed in natural language, automatically parses complex amounts and descriptions (including Indian numbering shorthand like `2k`, `1.5k`, `2 lakh`), categorizes transactions using a 4-layer hybrid AI classifier, persists records into SQLite, and displays financial analytics through an interactive, real-time 3D dashboard.

---

## 🌟 Key Features

### 1. Automatic Expense Categorization & NLP
- **Natural Language Parsing:** Enter expenses like:
  - `"2k for biryani"` → Amount: ₹2,000 | Category: Food | Description: Biryani
  - `"Bought Nike shoes for 3500"` → Amount: ₹3,500 | Category: Shopping | Description: Nike Shoes
  - `"Petrol 600"` → Amount: ₹600 | Category: Transport
  - `"Paid electricity bill 1200"` → Amount: ₹1,200 | Category: Bills
  - `"Dosa and coffee 150"` → Amount: ₹150 | Category: Food
  - `"Bought Python course for 999"` → Amount: ₹999 | Category: Education
  - `"Movie ticket 300"` → Amount: ₹300 | Category: Entertainment
  - `"Doctor consultation 500"` → Amount: ₹500 | Category: Health
  - `"Milk, eggs and vegetables 250"` → Amount: ₹250 | Category: Groceries
  - `"Haircut 150"` → Amount: ₹150 | Category: Personal Care
- **Multi-Expense Splitting:** Enter multiple expenses in a single line, e.g.:
  - `"500 petrol, 200 coffee, 1200 electricity bill"` → automatically parsed into 3 distinct transactions.
- **Indian Numbering Shorthand:** Full support for `2k`, `1.5k`, `2 lakh`, `1.25 cr`, `₹2,000`, `Rs 500`.

### 2. 4-Layer Hybrid Categorization Architecture
1. **Layer 1 (Rule-Based Classifier):** Configurable keywords, synonyms, and Indian merchants (Swiggy, Zomato, Uber, Ola, Amazon, Flipkart, Bescom, Blinkit, Zepto, etc.). Operates completely offline with zero external dependencies.
2. **Layer 2 (Local LLM via Ollama):** Interprets unfamiliar and ambiguous descriptions by prompting a local Ollama model (e.g. `qwen2.5:3b`) with structured JSON validation.
3. **Layer 3 (Confidence & Ambiguity Handling):** Auto-categorizes high-confidence matches (≥ 75%) and flags ambiguous entries for user review.
4. **Layer 4 (Learned User Corrections):** Whenever you edit a transaction's category, the system saves the mapping. User corrections take **highest precedence** over generic keywords for future transactions.

### 3. 3D Interactive Cosmos Dashboard (Three.js)
- **Central Financial Core:** Rotating 3D wireframe icosahedron with glowing nucleus and dual planetary orbit rings.
- **Dynamic Category Nodes:** Orbiting 3D crystal orbs whose radius and luminescence scale dynamically based on real database spending.
- **Interactive Raycasting:** Hovering over any orb displays a glassmorphism HUD tooltip with category metrics (Total spend, share %, transaction count). Clicking focuses the node.
- **Controls:** Rotation toggle (reduced-motion support), camera reset, and OrbitControls (drag to rotate, scroll to zoom).

### 4. Financial Analytics & Budgeting
- **Pandas & NumPy Engine:** Total income, total expenses, net balance, savings rate, and daily spend averages.
- **Interactive Plotly Visuals:** Category donut breakdown, daily spending & cumulative trend, and monthly cash flow.
- **Recurring Expense Detection:** Automatically identifies subscription and regular recurring bills based on frequency and low coefficient of variance.
- **Spending Anomaly Detection:** Statistical outlier detection using Interquartile Range (IQR) to flag unusually high individual transactions.
- **Budget Planning:** Set monthly category budgets with safe (<80%), warning (80-100%), and exceeded (>100%) visual meters.

### 5. Reports & Data Interchange
- **Matplotlib Report Export:** Download high-resolution PNG multi-panel chart report.
- **Executive Markdown Summary:** Generate and export structured executive summary reports.
- **CSV Import / Export:** Export transactions or import CSV statements with built-in duplicate detection.

---

## 🏗️ Project Architecture

```
Expense_tracker/
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── README.md                   # Project documentation
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── src/                        # Core business logic (UI-independent)
│   ├── __init__.py
│   ├── config.py               # Settings, categories, colors, Ollama config
│   ├── models.py               # Dataclass models (Transaction, Budget, ParsedExpense)
│   ├── database.py             # SQLite CRUD layer, indexing, transactions
│   ├── amount_parser.py        # Natural language amount & description parser
│   ├── categorizer.py          # 4-Layer hybrid classification engine
│   ├── transaction_service.py  # End-to-end transaction orchestrator & learning loop
│   ├── analytics.py            # Financial analytics (Pandas, NumPy, Plotly, Matplotlib)
│   ├── budget_manager.py       # Category & overall budget progress tracker
│   ├── insights.py             # Deterministic fact-based financial insights generator
│   └── csv_manager.py          # CSV import/export and duplicate detection
├── ui/                         # Presentation layer
│   ├── __init__.py
│   ├── styles.css              # Dark charcoal glassmorphism theme
│   ├── components.py           # Streamlit reusable UI card renderers
│   └── three_d_dashboard.py    # Three.js 3D Interactive Cosmos component
├── tests/                      # Automated test suite (39 unit tests)
│   ├── test_amount_parser.py
│   ├── test_categorizer.py
│   ├── test_database.py
│   ├── test_transactions.py
│   ├── test_analytics.py
│   ├── test_budgets.py
│   └── test_csv_and_insights.py
└── data/                       # Local SQLite storage directory
    ├── expenses.db
    └── .gitkeep
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.11** or higher.
- *(Optional)* [Ollama](https://ollama.com/) running locally with `qwen2.5:3b` for local language model assistance. The app works seamlessly offline if Ollama is not present.

### 2. Installation
Clone the repository and install the required dependencies:

```bash
cd Expense_tracker
pip install -r requirements.txt
```

### 3. Running the Application
Start the Streamlit application:

```bash
streamlit run app.py
```

The app will be available at: `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Run the complete test suite using `pytest`:

```bash
python -m pytest tests
```

Expected output:
```
============================= 39 passed in 1.73s =============================
```

The automated tests cover:
- Natural language amount extraction (`2k`, `1.5k`, `2 lakh`, `₹2,000`).
- Multi-expense splitting.
- All category classification rules (Food, Shopping, Transport, Bills, etc.).
- Ambiguous & unknown input handling.
- Learned user correction priority.
- SQLite transactions, batch inserts, and parameterized queries.
- Budget threshold calculations (Safe, Warning, Exceeded).
- Financial metrics (Income, Expenses, Net Cash Flow, Savings Rate).
- Statistical anomaly and recurring expense detection.
- CSV import, duplicate rejection, and PNG report generation.

---

## ⚙️ Configuration & Environment

You can configure environment variables in `.env` (refer to `.env.example`):

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DB_PATH` | `data/expenses.db` | Path to SQLite database file |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama local API endpoint |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Local LLM model for categorization |
| `DEFAULT_CURRENCY` | `INR` | Default currency code |
| `CURRENCY_SYMBOL` | `₹` | Currency symbol |

---

## 🛡️ License
MIT License. Built for modern personal wealth management.
