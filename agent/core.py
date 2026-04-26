import json
import re
from typing import Optional
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

from agent.config import Config
from agent.prompts import SYSTEM_PROMPT
from agent.result import AgentResult
from agent.tools import get_schema_tool, run_sql_tool, run_python_tool, generate_chart_tool
from agent.tools._data_store import data_store, clear as clear_store


class DataAnalystAgent:
    """
    Autonomous data analyst agent.
    Uses LangGraph ReAct agent with SQL, Pandas, and viz tools.
    """

    def __init__(self, verbose: Optional[bool] = None):
        Config.validate()
        self.verbose = verbose if verbose is not None else Config.VERBOSE
        self._tools = [get_schema_tool, run_sql_tool, run_python_tool, generate_chart_tool]
        self._graph = self._build_graph()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_graph(self):
        llm = Config.get_llm()
        return create_react_agent(
            model=llm,
            tools=self._tools,
            prompt=SYSTEM_PROMPT,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, question: str, chat_history: list = None) -> AgentResult:
        """
        Run the agent on a natural-language question.
        Returns an AgentResult with summary, SQL queries, DataFrames, and chart paths.
        """
        clear_store()

        messages = []
        for msg in (chat_history or []):
            messages.append(msg)
        messages.append(HumanMessage(content=question))

        try:
            result = self._graph.invoke(
                {"messages": messages},
                config={"recursion_limit": Config.MAX_ITERATIONS * 3},
            )
        except Exception as e:
            return AgentResult(question=question, summary="", error=str(e))

        all_messages = result.get("messages", [])

        # Last AI message is the final answer
        summary = ""
        for msg in reversed(all_messages):
            if hasattr(msg, "content") and msg.__class__.__name__ == "AIMessage":
                if isinstance(msg.content, str) and msg.content.strip():
                    summary = msg.content
                    break

        # Extract SQL and chart paths from tool messages
        sql_queries = []
        chart_paths = []
        intermediate_steps = []

        for msg in all_messages:
            cls = msg.__class__.__name__

            # Tool call inputs — extract SQL
            if cls == "AIMessage" and hasattr(msg, "tool_calls"):
                for tc in (msg.tool_calls or []):
                    name = tc.get("name", "")
                    args = tc.get("args", {})
                    if name == "run_sql" and args.get("query"):
                        sql_queries.append(args["query"])
                    intermediate_steps.append({"tool": name, "output": str(args)[:300]})

            # Tool outputs — extract chart paths
            if cls == "ToolMessage":
                content = msg.content or ""
                try:
                    data = json.loads(content)
                    if isinstance(data, dict) and data.get("path"):
                        chart_paths.append(data["path"])
                except (json.JSONDecodeError, TypeError):
                    matches = re.findall(r'"path":\s*"([^"]+)"', content)
                    chart_paths.extend(matches)

        dataframes = list(data_store.values())

        if self.verbose:
            print(f"\n[Agent] Tools used: {[s['tool'] for s in intermediate_steps]}")
            print(f"[Agent] SQL queries: {len(sql_queries)}, Charts: {len(chart_paths)}")

        return AgentResult(
            question=question,
            summary=summary,
            sql_queries=sql_queries,
            dataframes=dataframes,
            chart_paths=chart_paths,
            intermediate_steps=intermediate_steps,
        )

    def switch_provider(self, provider: str):
        """Hot-swap LLM provider ('openai' or 'anthropic') without reinstantiation."""
        provider = provider.lower()
        if provider not in ("openai", "anthropic"):
            raise ValueError("provider must be 'openai' or 'anthropic'")
        Config.LLM_PROVIDER = provider
        self._graph = self._build_graph()
        return self
