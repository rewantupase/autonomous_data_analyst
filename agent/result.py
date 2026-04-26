from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AgentResult:
    """Structured output from a single agent run."""
    question: str
    summary: str
    sql_queries: List[str] = field(default_factory=list)
    dataframes: List[object] = field(default_factory=list)   # List[pd.DataFrame]
    chart_paths: List[str] = field(default_factory=list)
    intermediate_steps: List[dict] = field(default_factory=list)
    error: Optional[str] = None

    def show_charts(self):
        """Open all generated chart files (works in notebook / local env)."""
        import os
        try:
            from IPython.display import display, Image
            for path in self.chart_paths:
                if os.path.exists(path):
                    display(Image(path))
        except ImportError:
            import subprocess, sys
            for path in self.chart_paths:
                if os.path.exists(path):
                    if sys.platform == "darwin":
                        subprocess.run(["open", path])
                    elif sys.platform.startswith("linux"):
                        subprocess.run(["xdg-open", path])
                    else:
                        os.startfile(path)

    def __repr__(self):
        return (
            f"AgentResult(\n"
            f"  question={self.question!r},\n"
            f"  summary={self.summary[:120]!r}{'...' if len(self.summary) > 120 else ''},\n"
            f"  sql_queries={len(self.sql_queries)},\n"
            f"  dataframes={len(self.dataframes)},\n"
            f"  charts={self.chart_paths}\n"
            f")"
        )
