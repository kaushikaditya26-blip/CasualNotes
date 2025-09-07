# Local shim so "from google import genai" works without editing app.py
# It imports the official google-generativeai package and exposes it
# as "genai" at the top-level module.

try:
    import google.generativeai as _genai
except Exception as _err:
    raise ImportError(
        "google.generativeai could not be imported. Install it with:\n"
        "    python -m pip install google-generativeai\n"
        f"Original error: {_err}"
    )

# expose as expected by your code: "from google import genai"
genai = _genai
__all__ = ["genai"]
