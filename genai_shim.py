"""
genai_shim.py — compatibility shim to provide `google.generativeai.models.generate(...)`
by forwarding to google.generativeai.GenerativeModel(...).generate(...)

Short-term fix: use while you migrate code to the new google.generativeai API.
"""
MODEL_NAME = "gemini-1.5-flash"

try:
    import google.generativeai as genai
except Exception as _err:
    genai = None

class _ModelsShim:
    def __init__(self, model_name=MODEL_NAME):
        self._model_name = model_name

    def generate(self, *args, **kwargs):
        """
        Forward to the new GenerativeModel API.
        The exact call signature may differ depending on your code.
        This shim forwards positional/keyword args to GenerativeModel(...).generate(...)
        """
        if genai is None:
            raise RuntimeError("google.generativeai not available")
        # instantiate the model and call generate
        model = genai.GenerativeModel(self._model_name)
        # try generate, fall back to .call if generate not present
        if hasattr(model, "generate"):
            return model.generate(*args, **kwargs)
        if hasattr(model, "call"):
            return model.call(*args, **kwargs)
        raise RuntimeError("GenerativeModel has no generate/call method")

# attach shim object as ".models" if it doesn't exist already
if genai is not None and not hasattr(genai, "models"):
    genai.models = _ModelsShim(MODEL_NAME)
