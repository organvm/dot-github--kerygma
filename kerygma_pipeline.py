"""Shim — delegates to the kerygma_pipeline package.

This file exists so that CI workflows can still run
``python kerygma_pipeline.py dispatch ...`` from the .github checkout.
All logic lives in the kerygma-pipeline package (pip install kerygma-pipeline).

The shim avoids circular imports by temporarily manipulating sys.path so
Python finds the installed package rather than this file.
"""
import importlib
import pathlib
import sys

# Temporarily hide this file's directory so importlib finds the *installed*
# kerygma_pipeline package, not this shim.
_this_dir = str(pathlib.Path(__file__).resolve().parent)
_saved_path = sys.path[:]
_saved_mod = sys.modules.pop("kerygma_pipeline", None)

sys.path = [p for p in sys.path if str(pathlib.Path(p).resolve()) != _this_dir]

try:
    _pkg = importlib.import_module("kerygma_pipeline")
finally:
    sys.path = _saved_path

# Replace the partially-initialized shim in sys.modules with the real package
sys.modules["kerygma_pipeline"] = _pkg

# Re-export everything into this module's namespace for `from kerygma_pipeline import X`
_ns = vars(_pkg)
for _name in list(_ns):
    if not _name.startswith("__"):
        globals()[_name] = _ns[_name]

# Key exports
KerygmaPipeline = _pkg.KerygmaPipeline  # noqa: F811
EVENT_TEMPLATE_MAP = _pkg.EVENT_TEMPLATE_MAP  # noqa: F811
main = _pkg.main  # noqa: F811

if __name__ == "__main__":
    _pkg.main()
