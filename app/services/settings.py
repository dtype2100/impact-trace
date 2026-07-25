from typing import Mapping

SECRET_NAMES = (
    "GENERATION_API_KEY",
    "EMBEDDING_API_KEY",
    "RERANK_API_KEY",
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
)

DEFAULTS = {
    "GENERATION_API_URL": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "GENERATION_MODEL": "gemini-3.6-flash",
    "EMBEDDING_API_URL": "https://generativelanguage.googleapis.com/v1beta/openai/embeddings",
    "EMBEDDING_MODEL": "gemini-embedding-2",
    "EMBEDDING_DIMENSION": "768",
    "RERANK_API_URL": "https://api.cohere.com/v2/rerank",
    "RERANK_MODEL": "rerank-v4.0-fast",
    "NEO4J_DATABASE": "neo4j",
}


class Settings:
    def __init__(self, values):
        self.values = values
        self.generation_url = values.get("GENERATION_API_URL", DEFAULTS["GENERATION_API_URL"])
        self.generation_model = values.get("GENERATION_MODEL", DEFAULTS["GENERATION_MODEL"])
        self.embedding_url = values.get("EMBEDDING_API_URL", DEFAULTS["EMBEDDING_API_URL"])
        self.embedding_model = values.get("EMBEDDING_MODEL", DEFAULTS["EMBEDDING_MODEL"])
        self.rerank_url = values.get("RERANK_API_URL", DEFAULTS["RERANK_API_URL"])
        self.rerank_model = values.get("RERANK_MODEL", DEFAULTS["RERANK_MODEL"])
        self.database = values.get("NEO4J_DATABASE", DEFAULTS["NEO4J_DATABASE"])
        try: self.embedding_dimension = int(values.get("EMBEDDING_DIMENSION", DEFAULTS["EMBEDDING_DIMENSION"]))
        except (TypeError, ValueError): self.embedding_dimension = None
        self.generation_key = values.get("GENERATION_API_KEY", "")
        self.embedding_key = values.get("EMBEDDING_API_KEY", "")
        self.rerank_key = values.get("RERANK_API_KEY", "")
    @classmethod
    def from_env(cls, env: Mapping[str, str]): return cls(dict(env))
    @property
    def mode(self):
        count = sum(bool(self.values.get(name)) for name in SECRET_NAMES)
        return "fixture" if count == 0 else "live" if count == len(SECRET_NAMES) and self.embedding_dimension and 128 <= self.embedding_dimension <= 3072 else "misconfigured"
