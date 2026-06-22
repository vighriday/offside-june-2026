"""OFFSIDE build-time engine.

Runs once, offline, on a clean build host. Ingests the IFAB Laws of the Game with
Docling, retrieves per-lens evidence, and uses IBM Granite (temperature 0) to write
frozen JSON fixtures that the web app reads at runtime.

The engine writes ``fixtures/`` and ``data/``; the web never imports this package.
"""

__version__ = "0.1.0"
