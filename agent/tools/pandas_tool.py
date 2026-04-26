_BLOCKED_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "http",
    "urllib", "ftplib", "smtplib", "pathlib", "glob",
    "ctypes", "multiprocessing", "threading", "signal",
    "pty", "atexit", "gc", "resource", "pwd", "grp",
}

def _safe_import(name, *args, **kwargs):
    top = name.split(".")[0]
    if top in _BLOCKED_MODULES:
        raise ImportError(f"Module \'{name}\' is not allowed in the analyst sandbox.")
    return __import__(name, *args, **kwargs)


import io
import traceback
import pandas as pd
import numpy as np
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from agent.tools._data_store import data_store


class PythonInput(BaseModel):
    code: str = Field(
        description=(
            "Python code to execute for data analysis. "
            "Access previous SQL results via `data_store` dict (e.g. data_store['sql_0']). "
            "Print results using print(). Store computed DataFrames back into data_store. "
            "Available: pandas as pd, numpy as np, data_store."
        )
    )


def run_python(code: str) -> str:
    """
    Execute Python/Pandas analysis code in a sandboxed namespace.
    Returns captured stdout + any errors.
    """
    stdout_capture = io.StringIO()

    namespace = {
        "pd": pd,
        "np": np,
        "data_store": data_store,
        "__builtins__": {
            "print": lambda *a, **kw: print(*a, **kw, file=stdout_capture),
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "round": round,
            "sorted": sorted,
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "isinstance": isinstance,
            "type": type,
            "repr": repr,
            "__import__": _safe_import,
            "hasattr": hasattr,
            "getattr": getattr,
            # Exception types
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "AttributeError": AttributeError,
            "Exception": Exception,
            "RuntimeError": RuntimeError,
            "StopIteration": StopIteration,
        },
    }

    try:
        exec(compile(code, "<analyst>", "exec"), namespace)
        output = stdout_capture.getvalue()

        # Collect any DataFrames created in namespace (skip built-in names)
        _skip = {"pd", "np", "data_store", "__builtins__"}
        new_dfs = {
            k: v for k, v in namespace.items()
            if isinstance(v, pd.DataFrame) and not k.startswith("_") and k not in _skip
        }
        for k, df in new_dfs.items():
            data_store[k] = df

        if not output.strip():
            output = "(code ran successfully, no printed output)"

        return output[:4000]
    except Exception:
        return f"PYTHON ERROR:\n{traceback.format_exc()}"


run_python_tool = StructuredTool.from_function(
    func=run_python,
    name="run_python",
    description=(
        "Execute Python (pandas/numpy) code for data analysis, EDA, statistics, "
        "or transformations. Access SQL results via data_store['sql_0'], etc. "
        "Use print() to output results. Returns captured stdout."
    ),
    args_schema=PythonInput,
)
