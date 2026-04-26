import os
import json
import uuid
import traceback
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from agent.config import Config
from agent.tools._data_store import data_store

sns.set_theme(style="whitegrid", palette="muted")

CHART_TYPES = ["bar", "line", "scatter", "histogram", "pie", "heatmap", "box"]


class ChartInput(BaseModel):
    chart_type: str = Field(
        description=f"Chart type. One of: {CHART_TYPES}"
    )
    store_key: str = Field(
        description="Key in data_store to use as source DataFrame (e.g. 'sql_0' or 'result_df')."
    )
    x_column: str = Field(description="Column name for the X axis (or labels for pie).")
    y_column: str = Field(
        default="",
        description="Column name for the Y axis. Leave empty for histogram/pie."
    )
    title: str = Field(default="", description="Chart title.")
    hue_column: str = Field(default="", description="Optional column for color grouping.")


def generate_chart(
    chart_type: str,
    store_key: str,
    x_column: str,
    y_column: str = "",
    title: str = "",
    hue_column: str = "",
) -> str:
    """Generate a chart from a DataFrame in data_store and save it to disk."""
    try:
        if store_key not in data_store:
            keys = list(data_store.keys())
            return f"ERROR: store_key '{store_key}' not found. Available keys: {keys}"

        df = data_store[store_key].copy()

        if x_column not in df.columns:
            return f"ERROR: column '{x_column}' not in DataFrame. Columns: {list(df.columns)}"
        if y_column and y_column not in df.columns:
            return f"ERROR: column '{y_column}' not in DataFrame. Columns: {list(df.columns)}"

        os.makedirs(Config.CHARTS_DIR, exist_ok=True)
        filename = f"chart_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(Config.CHARTS_DIR, filename)

        fig, ax = plt.subplots(figsize=(10, 6))
        chart_title = title or f"{chart_type.capitalize()} — {x_column}" + (f" vs {y_column}" if y_column else "")
        ax.set_title(chart_title, fontsize=14, fontweight="bold", pad=15)

        ct = chart_type.lower()

        if ct == "bar":
            hue = hue_column if hue_column and hue_column in df.columns else None
            sns.barplot(data=df, x=x_column, y=y_column, hue=hue, ax=ax)
            ax.set_xlabel(x_column)
            ax.set_ylabel(y_column)
            plt.xticks(rotation=30, ha="right")

        elif ct == "line":
            hue = hue_column if hue_column and hue_column in df.columns else None
            sns.lineplot(data=df, x=x_column, y=y_column, hue=hue, ax=ax, marker="o")
            ax.set_xlabel(x_column)
            ax.set_ylabel(y_column)

        elif ct == "scatter":
            hue = hue_column if hue_column and hue_column in df.columns else None
            sns.scatterplot(data=df, x=x_column, y=y_column, hue=hue, ax=ax, alpha=0.7)
            ax.set_xlabel(x_column)
            ax.set_ylabel(y_column)

        elif ct == "histogram":
            sns.histplot(data=df, x=x_column, kde=True, ax=ax)
            ax.set_xlabel(x_column)
            ax.set_ylabel("Count")

        elif ct == "pie":
            counts = df[x_column].value_counts() if not y_column else df.set_index(x_column)[y_column]
            counts = counts.head(10)
            ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=140)
            ax.axis("equal")

        elif ct == "heatmap":
            numeric_df = df.select_dtypes(include="number")
            corr = numeric_df.corr()
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax, linewidths=0.5)

        elif ct == "box":
            hue = hue_column if hue_column and hue_column in df.columns else None
            sns.boxplot(data=df, x=x_column, y=y_column, hue=hue, ax=ax)
            ax.set_xlabel(x_column)
            ax.set_ylabel(y_column)
            plt.xticks(rotation=30, ha="right")

        else:
            plt.close(fig)
            return f"ERROR: Unknown chart_type '{chart_type}'. Use one of {CHART_TYPES}."

        fig.tight_layout()
        fig.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close(fig)

        return json.dumps({"status": "ok", "path": filepath, "title": chart_title})

    except Exception:
        return f"CHART ERROR:\n{traceback.format_exc()}"


generate_chart_tool = StructuredTool.from_function(
    func=generate_chart,
    name="generate_chart",
    description=(
        "Generate and save a chart (bar, line, scatter, histogram, pie, heatmap, box). "
        "Reads data from data_store using store_key. Returns the file path of the saved chart."
    ),
    args_schema=ChartInput,
)
