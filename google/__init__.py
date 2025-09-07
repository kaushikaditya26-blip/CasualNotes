# Local shim so "from google import genai" works without editing app.py
try:
    import google.generativeai as _genai
except Exception as _err:
    raise ImportError(
        "google.generativeai could not be imported. Install it with: "
        "python -m pip install google-generativeai\n"
        f"Original error: {_err}"
    )

genai = _genai
__all__ = ["genai"]
