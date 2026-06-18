"""pytest configuration for the Data-Quality Audit tool.

Adds this project folder to sys.path so tests in tests/ can simply
`import audit` without any package-installation step.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
