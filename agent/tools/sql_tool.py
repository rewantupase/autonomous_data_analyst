import json
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from agent.config import Config


def _get_engine():
    return create_engine(Config.DATABASE_URL, connect_args={"check_same_thread": False})


# ── Schema introspection ──────────────────────────────────────────────────────

def get_schema(_: str = "") -> str:
    """Return a JSON description of all tables, columns, and types in the DB."""
    try:
        engine = _get_engine()
        inspector = inspect(engine)
        schema = {}
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            pk = inspector.get_pk_constraint(table_name).get("constrained_columns", [])
            fks = inspector.get_foreign_keys(table_name)
            schema[table_name] = {
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "primary_key": col["name"] in pk,
                    }
                    for col in columns
                ],
                "foreign_keys": [
                    {
                        "column": fk["constrained_columns"],
                        "references": f"{fk['referred_table']}.{fk['referred_columns']}",
                    }
                    for fk in fks
                ],
            }
        return json.dumps(schema, indent=2)
    except Exception as e:
        return f"ERROR getting schema: {e}"


class SQLInput(BaseModel):
    query: str = Field(description="A read-only SQL SELECT query to execute.")


def run_sql(query: str) -> str:
    """Execute a SQL SELECT query and return results as a JSON string."""
    # Safety check — block mutating statements
    forbidden = ["insert", "update", "delete", "drop", "alter", "create", "truncate"]
    q_lower = query.strip().lower()
    for kw in forbidden:
        if q_lower.startswith(kw) or f" {kw} " in q_lower:
            return f"ERROR: Mutating SQL statement blocked ({kw.upper()}). Only SELECT is allowed."

    try:
        engine = _get_engine()
        with engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn)

        if df.empty:
            return "Query returned 0 rows."

        # Store in shared store for downstream Python tool
        from agent.tools._data_store import data_store
        key = f"sql_{len(data_store)}"
        data_store[key] = df

        preview = df.head(50).to_dict(orient="records")
        return json.dumps({
            "rows": len(df),
            "columns": list(df.columns),
            "preview": preview,
            "store_key": key,
        }, default=str)
    except Exception as e:
        return f"SQL ERROR: {e}"


# ── LangChain tool wrappers ───────────────────────────────────────────────────

get_schema_tool = StructuredTool.from_function(
    func=get_schema,
    name="get_schema",
    description=(
        "Retrieve the full database schema: all tables, columns, data types, "
        "primary keys, and foreign keys. Call this FIRST before writing any SQL."
    ),
)

run_sql_tool = StructuredTool.from_function(
    func=run_sql,
    name="run_sql",
    description=(
        "Execute a read-only SQL SELECT query against the database. "
        "Returns row count, column names, and a preview of results. "
        "Results are also stored internally for use by run_python."
    ),
    args_schema=SQLInput,
)
