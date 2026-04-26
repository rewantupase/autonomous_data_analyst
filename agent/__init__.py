def __getattr__(name):
    if name == "DataAnalystAgent":
        from .core import DataAnalystAgent
        return DataAnalystAgent
    if name == "AgentResult":
        from .result import AgentResult
        return AgentResult
    raise AttributeError(f"module 'agent' has no attribute {name!r}")

__all__ = ["DataAnalystAgent", "AgentResult"]
