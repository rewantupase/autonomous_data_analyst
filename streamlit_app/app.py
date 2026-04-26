"""
Autonomous Data Analyst — Streamlit UI
Run: streamlit run streamlit_app/app.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

st.set_page_config(
    page_title="Data Analyst Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .main-header { font-size: 2rem; font-weight: 700; margin-bottom: 0.25rem; }
  .sub-header  { color: #888; font-size: 0.95rem; margin-bottom: 1.5rem; }
  .metric-row  { display: flex; gap: 1rem; margin: 1rem 0; }
  .sql-box     { background: #1e1e1e; color: #d4d4d4; padding: 1rem;
                 border-radius: 8px; font-family: monospace; font-size: 0.85rem;
                 white-space: pre-wrap; overflow-x: auto; }
  .step-item   { font-size: 0.8rem; color: #666; margin: 2px 0; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = None
if "history" not in st.session_state:
    st.session_state.history = []   # list of (question, AgentResult)
if "provider" not in st.session_state:
    st.session_state.provider = "openai"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    provider = st.selectbox(
        "LLM Provider",
        ["openai", "anthropic"],
        index=0 if st.session_state.provider == "openai" else 1,
    )

    if provider == "openai":
        api_key = st.text_input("OpenAI API Key", type="password",
                                value=os.getenv("OPENAI_API_KEY", ""))
        model = st.selectbox("Model", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
    else:
        api_key = st.text_input("Anthropic API Key", type="password",
                                value=os.getenv("ANTHROPIC_API_KEY", ""))
        model = st.selectbox("Model", ["claude-opus-4-5", "claude-sonnet-4-5"])

    db_url = st.text_input(
        "Database URL",
        value=os.getenv("DATABASE_URL", "sqlite:///./db/sample.db"),
    )

    verbose = st.checkbox("Verbose agent output", value=False)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔗 Connect", use_container_width=True):
            _connect(provider, api_key, model, db_url, verbose)
    with col2:
        if st.button("🌱 Seed DB", use_container_width=True):
            with st.spinner("Seeding sample database..."):
                try:
                    from db.seed import seed
                    seed()
                    st.success("Database seeded!")
                except Exception as e:
                    st.error(f"Seed failed: {e}")

    st.divider()
    st.markdown("### 💡 Sample questions")
    samples = [
        "Top 5 products by revenue",
        "Monthly revenue trend for 2023",
        "Revenue by customer region",
        "Correlation between age and spending",
        "Distribution of order amounts",
        "Most profitable product categories",
    ]
    for q in samples:
        if st.button(q, use_container_width=True, key=f"sample_{q}"):
            st.session_state["prefill"] = q

    st.divider()
    if st.button("🗑️ Clear history", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    # Status
    if st.session_state.agent:
        st.success(f"✅ Connected — {provider.upper()}")
    else:
        st.warning("Not connected. Press **Connect**.")


def _connect(provider, api_key, model, db_url, verbose):
    try:
        os.environ["LLM_PROVIDER"] = provider
        os.environ["DATABASE_URL"] = db_url
        if provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["OPENAI_MODEL"] = model
        else:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            os.environ["ANTHROPIC_MODEL"] = model

        from agent import DataAnalystAgent
        st.session_state.agent = DataAnalystAgent(verbose=verbose)
        st.session_state.provider = provider
        st.success(f"Connected to {provider.upper()} ({model})")
    except Exception as e:
        st.error(f"Connection failed: {e}")


# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">🤖 Autonomous Data Analyst</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Ask anything about your data in plain English.</p>', unsafe_allow_html=True)

# Pre-fill from sidebar sample click
prefill = st.session_state.pop("prefill", "")

with st.form("question_form", clear_on_submit=True):
    question = st.text_input(
        "Your question",
        value=prefill,
        placeholder="e.g. What are the top 5 products by revenue?",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("▶ Analyze", use_container_width=False, type="primary")

if submitted and question.strip():
    if not st.session_state.agent:
        st.error("Please configure and connect the agent in the sidebar first.")
    else:
        with st.spinner("Agent is thinking..."):
            result = st.session_state.agent.run(question.strip())
        st.session_state.history.append((question.strip(), result))
        st.rerun()

# ── History ───────────────────────────────────────────────────────────────────
for i, (q, result) in enumerate(reversed(st.session_state.history)):
    with st.expander(f"**Q:** {q}", expanded=(i == 0)):
        if result.error:
            st.error(result.error)
            continue

        # Answer
        st.markdown("### 📝 Answer")
        st.markdown(result.summary)

        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("SQL Queries", len(result.sql_queries))
        col2.metric("DataFrames", len(result.dataframes))
        col3.metric("Charts", len(result.chart_paths))

        # Charts
        if result.chart_paths:
            st.markdown("### 📊 Charts")
            chart_cols = st.columns(min(len(result.chart_paths), 2))
            for j, path in enumerate(result.chart_paths):
                if os.path.exists(path):
                    with chart_cols[j % 2]:
                        st.image(path, use_column_width=True)

        # Data preview
        if result.dataframes:
            st.markdown("### 🗃️ Data")
            tabs = st.tabs([f"DataFrame {k}" for k in range(len(result.dataframes))])
            for k, (tab, df) in enumerate(zip(tabs, result.dataframes)):
                with tab:
                    st.dataframe(df.head(100), use_container_width=True)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "⬇ Download CSV",
                        data=csv,
                        file_name=f"result_{i}_{k}.csv",
                        mime="text/csv",
                    )

        # SQL queries
        if result.sql_queries:
            st.markdown("### 🔍 SQL Executed")
            for j, sql in enumerate(result.sql_queries):
                st.markdown(f"**Query {j+1}**")
                st.code(sql, language="sql")

        # Agent steps
        if result.intermediate_steps:
            with st.expander("🔬 Agent reasoning steps"):
                for step in result.intermediate_steps:
                    st.markdown(
                        f'<div class="step-item"><b>{step["tool"]}</b> → {step["output"][:200]}</div>',
                        unsafe_allow_html=True,
                    )

# Empty state
if not st.session_state.history:
    st.info("👆 Ask a question above to get started. Try: *\"What are the top 5 products by revenue?\"*")
