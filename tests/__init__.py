import os

# Default trio env for tests
os.environ.setdefault("AI_FACTORY_ADVISOR_ENABLED", "true")
os.environ.setdefault("AI_FACTORY_PRIVACY_STRICT", "true")
os.environ.setdefault("AI_FACTORY_CONTEXT_TOPK", "3")
os.environ.setdefault("AI_FACTORY_CLOUD_BACKEND", "openai")
os.environ.setdefault("AI_FACTORY_CLOUD_MODEL", "gpt-4o")
os.environ.setdefault("AI_FACTORY_LOCAL_STRATEGIST_MODEL", "mistral:7b-q4_K_M")
os.environ.setdefault("AI_FACTORY_LOCAL_MEMORY_MODEL", "phi3:3b-q4")
os.environ.setdefault("AI_FACTORY_LOCAL_EXECUTION_MODEL", "phi:mini")
os.environ.setdefault("AI_FACTORY_LOCAL_STRATEGIST_URL", "http://127.0.0.1:11434")
os.environ.setdefault("AI_FACTORY_LOCAL_MEMORY_URL", "http://127.0.0.1:11435")
os.environ.setdefault("AI_FACTORY_LOCAL_EXECUTION_URL", "http://127.0.0.1:11436")
os.environ.setdefault("AI_FACTORY_LOCAL_TIMEOUT", "2")
os.environ.setdefault("AI_FACTORY_CLOUD_TIMEOUT", "2")
os.environ.setdefault("AI_FACTORY_EMBEDDINGS_BACKEND", "FAKE")
os.environ.setdefault("ADMIN_MODE", "true")
os.environ.setdefault("FACTORY_VERSION", "v3.1.1-memory-admin")
