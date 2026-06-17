"""pytest configuration for the Email Marketing SQL project.

Adds this project folder to sys.path so tests in tests/ can simply
`import build_database` and `import run_queries` without any package
installation step.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
