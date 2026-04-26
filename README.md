# Autonomous Data Analyst Agent

> A fully agentic pipeline that transforms natural language prompts into database queries, exploratory analysis, and visual insights — automatically.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.1%2B-1C3C3C?style=flat-square&logo=chainlink&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991?style=flat-square&logo=openai&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-PostgreSQL%20%2F%20SQLite-336791?style=flat-square&logo=postgresql&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?style=flat-square&logo=pandas&logoColor=white)

---

## Overview

The Autonomous Data Analyst Agent is an agentic AI system that lets anyone — regardless of SQL or Python expertise — run complex, multi-step data analysis simply by describing what they want in plain English.

The agent autonomously decides which tools to call, in what order, and how to combine results — all without human intervention at each step.

**Key results:**
- **92% accuracy** on multi-step query benchmarks
- **70% reduction** in time-to-insight vs. manual analysis workflows

---

##  Architecture

```
User Prompt (Natural Language)
        │
        ▼
  ┌─────────────┐
  │  LangChain  │  ← Agent Orchestrator (ReAct / Tool-Calling)
  │    Agent    │
  └──────┬──────┘
         │  decides which tools to invoke
    ┌────┴────┬──────────────┐
    ▼         ▼              ▼
 SQL Tool  Python/Pandas  Viz Tool
 (query    (EDA, stats,   (charts,
  DB)       transforms)    plots)
    │         │              │
    └────┬────┴──────────────┘
         ▼
  Synthesized Insight
  (text + visuals)
```

---

##  Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangChain (ReAct Agent) |
| LLM Backend | OpenAI GPT-4 |
| Data Querying | SQLAlchemy + raw SQL |
| Data Processing | Pandas, NumPy |
| Visualization | Matplotlib, Seaborn, Plotly |
| Database Support | PostgreSQL, SQLite, MySQL |
| Environment | Python 3.10+ |

---

## Features

- **Natural Language → SQL**: Converts plain English questions into valid, optimized SQL queries
- **Autonomous EDA**: Runs exploratory data analysis (distributions, correlations, outliers) without being told how
- **Multi-step Reasoning**: Chains tool calls across query → analyze → visualize in a single prompt
- **Self-correcting**: Catches SQL errors and retries with corrected queries automatically
- **Insight Generation**: Produces written summaries alongside charts and statistics
- **Schema-Aware**: Introspects database schema at runtime — no hardcoding required

---

##  Getting Started

### Prerequisites

```bash
python >= 3.10
pip install -r requirements.txt
```

### Installation

```bash
git clone https://github.com/yourusername/autonomous-data-analyst.git
cd autonomous-data-analyst
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///your_database.db   # or postgresql://user:pass@host/db
```

### Usage

```python
from agent import DataAnalystAgent

agent = DataAnalystAgent()

result = agent.run("What are the top 5 products by revenue last quarter, and how did their sales trend month over month?")

print(result.summary)
result.show_charts()
```

---

##  Project Structure

```
autonomous-data-analyst/
├── agent/
│   ├── __init__.py
│   ├── core.py            # Main agent loop (LangChain ReAct)
│   ├── tools/
│   │   ├── sql_tool.py    # SQL query execution + schema introspection
│   │   ├── pandas_tool.py # EDA, statistics, transformations
│   │   └── viz_tool.py    # Chart generation (matplotlib/plotly)
│   └── prompts.py         # System prompts and few-shot examples
├── db/
│   └── schema.sql         # Sample schema for testing
├── notebooks/
│   └── demo.ipynb         # Interactive walkthrough
├── tests/
│   └── test_agent.py      # Benchmark suite (92% accuracy set)
├── .env.example
├── requirements.txt
└── README.md
```

---

##  Benchmark Results

Evaluated on a custom suite of 50 multi-step analytical queries across 3 database schemas:

| Metric | Score |
|---|---|
| Query Accuracy (multi-step) | 92% |
| Single-step SQL Accuracy | 97% |
| EDA Completeness Score | 89% |
| Avg. Time-to-Insight | ~18s |
| vs. Manual Baseline | **70% faster** |

---

##  Roadmap

- [ ] Add support for CSV/Excel file uploads as ad-hoc data sources
- [ ] Streaming output (token-by-token insights as they're generated)
- [ ] Memory: persist conversation context across sessions
- [ ] Web UI (Streamlit or Gradio frontend)
- [ ] LangSmith tracing integration for observability

---

##  License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with LangChain, OpenAI, and a lot of `pd.DataFrame` calls.*
