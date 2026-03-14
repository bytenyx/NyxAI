"""NyxAI - An Agentic AIOps System.

NyxAI is an intelligent AIOps platform for anomaly detection, root cause analysis,
and auto-recovery using LLM-powered agents.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("nyxai")
except PackageNotFoundError:
    # Package is not installed, use default version
    __version__ = "0.1.0"

__all__ = ["__version__"]
