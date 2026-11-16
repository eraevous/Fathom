"""Fathom's local data-to-decisions slice.

Notebook API (spec 029): ``from fathom.api import profile, liftoff``. ``fathom.profile`` is also
exposed here, lazily, so ``import fathom`` and the CLI stay light. ``fathom.liftoff`` cannot be
the function: it is the name of the existing ``fathom.liftoff`` module, which the import system
rebinds on the package whenever that module loads. Use ``fathom.api.liftoff``.

Opt-in SQL source (spec 030): ``fathom.profile_query(conn, query, limit=...)`` profiles the rows of
a query on a DB-API connection the caller opened. Fathom imports no database driver.
"""

__version__ = "0.1.0"


def __getattr__(name):
    if name in ("profile", "profile_query"):
        from . import api
        return getattr(api, name)
    raise AttributeError(f"module 'fathom' has no attribute {name!r}")
