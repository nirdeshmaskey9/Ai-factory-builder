class SentenceTransformerEmbeddingFunction:
    """
    Lightweight stub compatible with the interface Chroma expects.
    It accepts text inputs and returns a list of embedding vectors when called.
    In this stub, we simply return zero-vectors to avoid heavyweight model loads.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name

    def __call__(self, inputs):
        # Return same-length zero vectors; Chroma stub ignores them.
        return [[0.0] * 128 for _ in inputs]

