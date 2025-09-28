import os

from collections.abc import Generator

import openai

from memos.configs.llm import AzureLLMConfig, OpenAILLMConfig
from memos.llms.base import BaseLLM
from memos.llms.utils import remove_thinking_tags
from memos.log import get_logger
from memos.types import MessageList


logger = get_logger(__name__)


class OpenAILLM(BaseLLM):
    """OpenAI LLM class."""

    def __init__(self, config: OpenAILLMConfig):
        self.config = config
        self.client = openai.Client(api_key=config.api_key, base_url=config.api_base)

    def generate(self, messages: MessageList) -> str:
        """Generate a response from OpenAI LLM."""
        model_name = self.config.model_name_or_path
        is_gpt5_family = model_name.startswith("gpt-5")
        # Build kwargs conditionally to support gpt-5* models requiring max_completion_tokens
        create_kwargs = {
            "model": model_name,
            "messages": messages,
            "extra_body": self.config.extra_body,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        # GPT-5 models: enforce API constraints (no top_p/logprobs; temperature must be 1)
        if is_gpt5_family:
            create_kwargs["temperature"] = 1
            if "top_p" in create_kwargs:
                create_kwargs.pop("top_p")
            # Sanitize extra_body for unsupported sampling/logprob fields
            if isinstance(create_kwargs.get("extra_body"), dict):
                for k in ["top_p", "top_logprobs", "logprobs", "logit_bias"]:
                    create_kwargs["extra_body"].pop(k, None)
        if is_gpt5_family:
            # Use explicit max_completion_tokens if provided; otherwise fallback to max_tokens
            max_comp = getattr(self.config, "max_completion_tokens", None)
            if max_comp is None:
                max_comp = getattr(self.config, "max_tokens", None)
            if max_comp is not None:
                create_kwargs["max_completion_tokens"] = max_comp
        else:
            create_kwargs["max_tokens"] = self.config.max_tokens
            create_kwargs["top_p"] = self.config.top_p

        try:
            response = self.client.chat.completions.create(**create_kwargs)
        except Exception as e:  # Fallback on invalid model
            msg = str(e).lower()
            if "invalid model" in msg or "model_not_found" in msg:
                fallback_model = os.getenv("MOS_FALLBACK_MODEL", "gpt-4o-mini")
                logger.warning(
                    f"Model '{model_name}' not available. Falling back to '{fallback_model}'. Error: {e!s}"
                )
                # Reset kwargs for non-gpt5 model
                fallback_kwargs = {
                    "model": fallback_model,
                    "messages": messages,
                    "extra_body": self.config.extra_body,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                }
                try:
                    response = self.client.chat.completions.create(**fallback_kwargs)
                except Exception:
                    raise
            else:
                raise
        logger.info(f"Response from OpenAI: {response.model_dump_json()}")
        response_content = response.choices[0].message.content
        if self.config.remove_think_prefix:
            return remove_thinking_tags(response_content)
        else:
            return response_content

    def generate_stream(self, messages: MessageList, **kwargs) -> Generator[str, None, None]:
        """Stream response from OpenAI LLM with optional reasoning support."""
        model_name = self.config.model_name_or_path
        is_gpt5_family = model_name.startswith("gpt-5")

        # Build kwargs conditionally to support gpt-5* models requiring max_completion_tokens
        create_kwargs = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "extra_body": self.config.extra_body,
            "temperature": self.config.temperature,
        }

        # GPT-5 models: enforce API constraints (no top_p/logprobs; temperature must be 1)
        if is_gpt5_family:
            create_kwargs["temperature"] = 1
            # Remove unsupported sampling fields
            if "top_p" in create_kwargs:
                create_kwargs.pop("top_p")
            if isinstance(create_kwargs.get("extra_body"), dict):
                for k in ["top_p", "top_logprobs", "logprobs", "logit_bias"]:
                    create_kwargs["extra_body"].pop(k, None)
            # Use explicit max_completion_tokens if provided; otherwise fallback to max_tokens
            max_comp = getattr(self.config, "max_completion_tokens", None)
            if max_comp is None:
                max_comp = getattr(self.config, "max_tokens", None)
            if max_comp is not None:
                create_kwargs["max_completion_tokens"] = max_comp
        else:
            create_kwargs["max_tokens"] = self.config.max_tokens

        try:
            response = self.client.chat.completions.create(**create_kwargs)
        except Exception as e:
            msg = str(e).lower()
            if "invalid model" in msg or "model_not_found" in msg:
                fallback_model = os.getenv("MOS_FALLBACK_MODEL", "gpt-4o-mini")
                logger.warning(
                    f"Model '{model_name}' not available for streaming. Falling back to '{fallback_model}'. Error: {e!s}"
                )
                fallback_kwargs = {
                    "model": fallback_model,
                    "messages": messages,
                    "stream": True,
                    "extra_body": self.config.extra_body,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                }
                response = self.client.chat.completions.create(**fallback_kwargs)
            else:
                raise

        reasoning_started = False

        for chunk in response:
            delta = chunk.choices[0].delta

            # Support for custom 'reasoning_content' (if present in OpenAI-compatible models like Qwen)
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                if not reasoning_started and not self.config.remove_think_prefix:
                    yield "<think>"
                    reasoning_started = True
                yield delta.reasoning_content
            elif hasattr(delta, "content") and delta.content:
                if reasoning_started and not self.config.remove_think_prefix:
                    yield "</think>"
                    reasoning_started = False
                yield delta.content

        # Ensure we close the <think> block if not already done
        if reasoning_started and not self.config.remove_think_prefix:
            yield "</think>"


class AzureLLM(BaseLLM):
    """Azure OpenAI LLM class."""

    def __init__(self, config: AzureLLMConfig):
        self.config = config
        self.client = openai.AzureOpenAI(
            azure_endpoint=config.base_url,
            api_version=config.api_version,
            api_key=config.api_key,
        )

    def generate(self, messages: MessageList) -> str:
        """Generate a response from Azure OpenAI LLM."""
        response = self.client.chat.completions.create(
            model=self.config.model_name_or_path,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
        )
        logger.info(f"Response from Azure OpenAI: {response.model_dump_json()}")
        response_content = response.choices[0].message.content
        if self.config.remove_think_prefix:
            return remove_thinking_tags(response_content)
        else:
            return response_content

    def generate_stream(self, messages: MessageList, **kwargs) -> Generator[str, None, None]:
        raise NotImplementedError
