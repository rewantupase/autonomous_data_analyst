"""
Test suite for the Autonomous Data Analyst Agent.
Uses a seeded in-memory SQLite DB — no API keys needed for tool-level tests.
"""
import os
import pytest
import sqlite3
import pandas as pd

os.environ.setdefault("DATABASE_URL", "sqlite:///./db/sample.db")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "test-key")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_data_store():
    from agent.tools._data_store import clear
    clear()
    yield
    clear()


@pytest.fixture(scope="session", autouse=True)
def seed_test_db():
    """Seed the DB once for the whole test session."""
    try:
        from db.seed import seed
        seed()
    except Exception:
        pass


# ── SQL Tool Tests ─────────────────────────────────────────────────────────────

class TestSQLTool:
    def test_get_schema_returns_json(self):
        from agent.tools.sql_tool import get_schema
        import json
        result = get_schema()
        schema = json.loads(result)
        assert "customers" in schema
        assert "orders" in schema
        assert "products" in schema
        assert "order_items" in schema

    def test_get_schema_columns(self):
        from agent.tools.sql_tool import get_schema
        import json
        schema = json.loads(get_schema())
        col_names = [c["name"] for c in schema["customers"]["columns"]]
        assert "id" in col_names
        assert "first_name" in col_names
        assert "region" in col_names

    def test_run_sql_basic_select(self):
        from agent.tools.sql_tool import run_sql
        import json
        result = json.loads(run_sql("SELECT * FROM customers LIMIT 5"))
        assert result["rows"] == 5
        assert "first_name" in result["columns"]

    def test_run_sql_stores_dataframe(self):
        from agent.tools.sql_tool import run_sql
        from agent.tools._data_store import data_store
        import json
        result = json.loads(run_sql("SELECT * FROM products LIMIT 10"))
        key = result["store_key"]
        assert key in data_store
        assert len(data_store[key]) == 10

    def test_run_sql_blocks_delete(self):
        from agent.tools.sql_tool import run_sql
        result = run_sql("DELETE FROM customers WHERE id=1")
        assert "ERROR" in result
        assert "blocked" in result.lower()

    def test_run_sql_blocks_drop(self):
        from agent.tools.sql_tool import run_sql
        result = run_sql("DROP TABLE customers")
        assert "ERROR" in result

    def test_run_sql_empty_result(self):
        from agent.tools.sql_tool import run_sql
        result = run_sql("SELECT * FROM customers WHERE id = -999")
        assert "0 rows" in result

    def test_run_sql_invalid_query(self):
        from agent.tools.sql_tool import run_sql
        result = run_sql("SELECT * FROM nonexistent_table")
        assert "ERROR" in result or "error" in result.lower()

    def test_run_sql_aggregation(self):
        from agent.tools.sql_tool import run_sql
        import json
        result = json.loads(run_sql(
            "SELECT category, COUNT(*) as count, AVG(price) as avg_price "
            "FROM products GROUP BY category ORDER BY count DESC"
        ))
        assert result["rows"] > 0
        assert "category" in result["columns"]
        assert "avg_price" in result["columns"]


# ── Pandas Tool Tests ─────────────────────────────────────────────────────────

class TestPandasTool:
    def test_run_python_basic(self):
        from agent.tools.pandas_tool import run_python
        result = run_python("print(1 + 1)")
        assert "2" in result

    def test_run_python_with_dataframe(self):
        from agent.tools._data_store import data_store
        import pandas as pd
        data_store["test_df"] = pd.DataFrame({
            "product": ["A", "B", "C"],
            "revenue": [100.0, 200.0, 150.0],
        })
        from agent.tools.pandas_tool import run_python
        result = run_python(
            "df = data_store['test_df']\n"
            "print(df['revenue'].sum())"
        )
        assert "450" in result

    def test_run_python_stores_new_df(self):
        from agent.tools._data_store import data_store
        from agent.tools.pandas_tool import run_python
        run_python(
            "import pandas as pd\n"
            "result_df = pd.DataFrame({'x': [1,2,3]})"
        )
        assert "result_df" in data_store

    def test_run_python_catches_errors(self):
        from agent.tools.pandas_tool import run_python
        result = run_python("raise ValueError('intentional test error')")
        assert "PYTHON ERROR" in result
        assert "intentional test error" in result

    def test_run_python_no_dangerous_imports(self):
        from agent.tools.pandas_tool import run_python
        result = run_python("import os; os.system('echo hacked')")
        assert "PYTHON ERROR" in result

    def test_run_python_statistics(self):
        from agent.tools._data_store import data_store
        import pandas as pd
        data_store["nums"] = pd.DataFrame({"value": list(range(1, 101))})
        from agent.tools.pandas_tool import run_python
        result = run_python(
            "df = data_store['nums']\n"
            "print(df['value'].mean())\n"
            "print(df['value'].std())"
        )
        assert "50.5" in result


# ── Viz Tool Tests ────────────────────────────────────────────────────────────

class TestVizTool:
    def test_bar_chart_creates_file(self, tmp_path):
        from agent.tools._data_store import data_store
        from agent.tools.viz_tool import generate_chart
        from agent.config import Config
        import pandas as pd, json

        Config.CHARTS_DIR = str(tmp_path)
        data_store["bar_df"] = pd.DataFrame({
            "category": ["A", "B", "C"],
            "revenue":  [100, 200, 150],
        })
        result = json.loads(generate_chart("bar", "bar_df", "category", "revenue", "Test Bar"))
        assert result["status"] == "ok"
        assert os.path.exists(result["path"])

    def test_missing_store_key(self):
        from agent.tools.viz_tool import generate_chart
        result = generate_chart("bar", "missing_key", "x", "y")
        assert "ERROR" in result

    def test_missing_column(self, tmp_path):
        from agent.tools._data_store import data_store
        from agent.tools.viz_tool import generate_chart
        from agent.config import Config
        import pandas as pd

        Config.CHARTS_DIR = str(tmp_path)
        data_store["df2"] = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = generate_chart("bar", "df2", "nonexistent_col", "b")
        assert "ERROR" in result

    def test_histogram(self, tmp_path):
        from agent.tools._data_store import data_store
        from agent.tools.viz_tool import generate_chart
        from agent.config import Config
        import pandas as pd, json, numpy as np

        Config.CHARTS_DIR = str(tmp_path)
        data_store["hist_df"] = pd.DataFrame({"value": np.random.normal(50, 10, 100)})
        result = json.loads(generate_chart("histogram", "hist_df", "value"))
        assert result["status"] == "ok"

    def test_heatmap(self, tmp_path):
        from agent.tools._data_store import data_store
        from agent.tools.viz_tool import generate_chart
        from agent.config import Config
        import pandas as pd, json, numpy as np

        Config.CHARTS_DIR = str(tmp_path)
        data_store["heat_df"] = pd.DataFrame(np.random.rand(20, 4), columns=["a","b","c","d"])
        result = json.loads(generate_chart("heatmap", "heat_df", "a"))
        assert result["status"] == "ok"


# ── Config Tests ──────────────────────────────────────────────────────────────

class TestConfig:
    def test_openai_provider(self):
        from agent.config import Config
        Config.LLM_PROVIDER = "openai"
        Config.OPENAI_API_KEY = "sk-test"
        llm = Config.get_llm()
        assert "openai" in type(llm).__module__.lower()

    def test_anthropic_provider(self):
        from agent.config import Config
        Config.LLM_PROVIDER = "anthropic"
        Config.ANTHROPIC_API_KEY = "sk-ant-test"
        llm = Config.get_llm()
        assert "anthropic" in type(llm).__module__.lower()

    def test_validate_raises_without_key(self):
        from agent.config import Config
        Config.LLM_PROVIDER = "openai"
        original = Config.OPENAI_API_KEY
        Config.OPENAI_API_KEY = ""
        with pytest.raises(EnvironmentError):
            Config.validate()
        Config.OPENAI_API_KEY = original
