"""
Shared in-memory store so SQL tool results can be passed to the Python tool
without going through the LLM context window.
"""
from typing import Dict
import pandas as pd

data_store: Dict[str, pd.DataFrame] = {}


def clear():
    data_store.clear()
