import os

from openai import AzureOpenAI as AzureClient
from openai import OpenAI as OpenAIClient

from memos.configs.embedder import UniversalAPIEmbedderConfig
from memos.embedders.base import BaseEmbedder
from memos.log import get_logger


class UniversalAPIEmbedder(BaseEmbedder):
    def __init__(self, config: UniversalAPIEmbedderConfig):
        self.provider = config.provider
        self.config = config
        self.logger = get_logger(__name__)

        if self.provider == "openai":
            self.client = OpenAIClient(api_key=config.api_key, base_url=config.base_url)
        elif self.provider == "azure":
            self.client = AzureClient(
                azure_endpoint=config.base_url,
                api_version="2024-03-01-preview",
                api_key=config.api_key,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.provider == "openai" or self.provider == "azure":
            model_name = getattr(self.config, "model_name_or_path", "text-embedding-3-large")
            if isinstance(model_name, str):
                model_name = model_name.strip()
            try:
                response = self.client.embeddings.create(
                    model=model_name,
                    input=texts,
                )
            except Exception as e:
                msg = str(e).lower()
                if ("invalid model" in msg) or ("model_not_found" in msg):
                    # Fallback to a safe default embedding model
                    fallback_model = os.getenv(
                        "MOS_EMBED_FALLBACK_MODEL", "text-embedding-3-large"
                    ).strip()
                    self.logger.warning(
                        f"Embedding model '{model_name}' not available. Falling back to '{fallback_model}'. Error: {e!s}"
                    )
                    response = self.client.embeddings.create(
                        model=fallback_model,
                        input=texts,
                    )
                else:
                    raise
            return [r.embedding for r in response.data]
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
