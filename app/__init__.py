"""Package marker for the `app` package.

Why: Establishes `app` as an importable Python package to support
modularization, dependency injection, and future Agent/Guardrails
integration without refactoring.
"""

__all__ = [
    "main",
    "rag_engine",
    "supabase_client",
]
