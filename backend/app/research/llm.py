"""Model adapters. The vendor is selected with MODEL_PROVIDER."""

from __future__ import annotations

import re
from typing import Protocol

import httpx

from app.research.errors import ModelError, TransientFailure, retry

BACKBOARD_MESSAGES_URL = "https://app.backboard.io/api/threads/messages"
GEMMA_API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
_GEMMA_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_BACKBOARD_PROVIDER = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class ModelClient(Protocol):
    def complete(self, *, system: str, user: str) -> str:
        """Return the model's raw text. Callers validate it before any guide is stored."""


def _model_status(status: int) -> ModelError:
    if status in {401, 403}:
        return ModelError(
            "The model API rejected the API key. Check MODEL_API_KEY and MODEL_PROVIDER.",
            "model_failed",
        )
    if status in {429, 500, 502, 503, 504}:
        return TransientFailure("The model API did not respond.", "model_failed")
    return ModelError("The model API rejected the request.", "model_failed")


def _openai_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return ""


def _text_from_openai(payload: object) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]  # type: ignore[index]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelError("The model API returned an unreadable response.", "model_failed") from exc
    text = _openai_text(content).strip()
    if not text:
        raise ModelError("The model API returned an empty response.", "model_failed")
    return text


def _text_from_anthropic(payload: object) -> str:
    try:
        blocks = payload["content"]  # type: ignore[index]
    except (KeyError, TypeError) as exc:
        raise ModelError("The model API returned an unreadable response.", "model_failed") from exc
    if not isinstance(blocks, list):
        raise ModelError("The model API returned an unreadable response.", "model_failed")
    parts = [block.get("text", "") for block in blocks if isinstance(block, dict) and block.get("type") == "text"]
    content = "".join(part for part in parts if isinstance(part, str)).strip()
    if not content:
        raise ModelError("The model API returned an empty response.", "model_failed")
    return content


class OpenAIModel:
    def __init__(self, api_key: str, model: str, *, timeout: float = 45, transport: httpx.BaseTransport | None = None) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._transport = transport

    def complete(self, *, system: str, user: str) -> str:
        def once() -> str:
            try:
                with httpx.Client(timeout=self._timeout, transport=self._transport, trust_env=False) as client:
                    response = client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self._api_key}"},
                        json={
                            "model": self._model,
                            "temperature": 0,
                            "response_format": {"type": "json_object"},
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user", "content": user},
                            ],
                        },
                    )
            except httpx.TimeoutException as exc:
                raise TransientFailure("The model API timed out.", "model_failed") from exc
            except httpx.TransportError as exc:
                raise TransientFailure("The model API could not be reached.", "model_failed") from exc
            if response.status_code >= 400:
                raise _model_status(response.status_code)
            try:
                return _text_from_openai(response.json())
            except ValueError as exc:
                raise ModelError("The model API returned an unreadable response.", "model_failed") from exc

        return retry(once)


class AnthropicModel:
    def __init__(self, api_key: str, model: str, *, timeout: float = 45, transport: httpx.BaseTransport | None = None) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._transport = transport

    def complete(self, *, system: str, user: str) -> str:
        def once() -> str:
            try:
                with httpx.Client(timeout=self._timeout, transport=self._transport, trust_env=False) as client:
                    response = client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": self._api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        },
                        json={
                            "model": self._model,
                            "max_tokens": 4096,
                            "temperature": 0,
                            "system": system,
                            "messages": [{"role": "user", "content": user}],
                        },
                    )
            except httpx.TimeoutException as exc:
                raise TransientFailure("The model API timed out.", "model_failed") from exc
            except httpx.TransportError as exc:
                raise TransientFailure("The model API could not be reached.", "model_failed") from exc
            if response.status_code >= 400:
                raise _model_status(response.status_code)
            try:
                return _text_from_anthropic(response.json())
            except ValueError as exc:
                raise ModelError("The model API returned an unreadable response.", "model_failed") from exc

        return retry(once)


def _plain_label(value: str, *, label: str) -> str:
    if not value or len(value) > 200 or any(character.isspace() or ord(character) < 32 for character in value):
        raise ModelError(f"The {label} is not a usable model id. Check MODEL_NAME.", "model_failed")
    return value


def _text_from_backboard(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ModelError("The model API returned an unreadable response.", "model_failed")
    content = payload.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ModelError("The model API returned an empty response.", "model_failed")
    return content.strip()


def _text_from_gemma(payload: object) -> str:
    try:
        parts = payload["candidates"][0]["content"]["parts"]  # type: ignore[index]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelError("The model API returned an unreadable response.", "model_failed") from exc
    if not isinstance(parts, list):
        raise ModelError("The model API returned an unreadable response.", "model_failed")
    texts: list[str] = []
    for part in parts:
        if not isinstance(part, dict) or part.get("thought") is True:
            continue
        text = part.get("text")
        if isinstance(text, str):
            texts.append(text)
    content = "".join(texts).strip()
    if not content:
        raise ModelError("The model API returned an empty response.", "model_failed")
    return content


class BackboardModel:
    """One Backboard key can call OpenAI, Gemma, and other upstream models."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        llm_provider: str,
        timeout: float = 45,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._llm_provider = llm_provider
        self._timeout = timeout
        self._transport = transport

    def complete(self, *, system: str, user: str) -> str:
        provider = self._llm_provider
        if _BACKBOARD_PROVIDER.fullmatch(provider) is None:
            raise ModelError(
                "The Backboard upstream is not recognized. Set BACKBOARD_LLM_PROVIDER to a provider such as openai or google.",
                "model_failed",
            )
        model_name = _plain_label(self._model, label="Backboard model")

        def once() -> str:
            try:
                with httpx.Client(timeout=self._timeout, transport=self._transport, trust_env=False) as client:
                    response = client.post(
                        BACKBOARD_MESSAGES_URL,
                        headers={"X-API-Key": self._api_key, "Content-Type": "application/json"},
                        json={
                            "content": user,
                            "system_prompt": system,
                            "llm_provider": provider,
                            "model_name": model_name,
                            "stream": False,
                            "memory": "off",
                            "web_search": "off",
                            "json_output": True,
                        },
                    )
            except httpx.TimeoutException as exc:
                raise TransientFailure("The model API timed out.", "model_failed") from exc
            except httpx.TransportError as exc:
                raise TransientFailure("The model API could not be reached.", "model_failed") from exc
            if response.status_code >= 400:
                raise _model_status(response.status_code)
            try:
                return _text_from_backboard(response.json())
            except ValueError as exc:
                raise ModelError("The model API returned an unreadable response.", "model_failed") from exc

        return retry(once)


class GemmaModel:
    """Hosted Gemma on the Gemini API. The default model is gemma-4-26b-a4b-it."""

    def __init__(self, api_key: str, model: str, *, timeout: float = 45, transport: httpx.BaseTransport | None = None) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._transport = transport

    def complete(self, *, system: str, user: str) -> str:
        if _GEMMA_MODEL_ID.fullmatch(self._model) is None:
            raise ModelError(
                "The Gemma model id is not recognized. Set MODEL_NAME to a Gemini API model such as gemma-4-26b-a4b-it.",
                "model_failed",
            )
        url = f"{GEMMA_API_ROOT}/{self._model}:generateContent"

        def once() -> str:
            try:
                with httpx.Client(timeout=self._timeout, transport=self._transport, trust_env=False) as client:
                    response = client.post(
                        url,
                        headers={"x-goog-api-key": self._api_key, "Content-Type": "application/json"},
                        json={
                            "systemInstruction": {"parts": [{"text": system}]},
                            "contents": [{"role": "user", "parts": [{"text": user}]}],
                            "generationConfig": {
                                "temperature": 0,
                                "responseMimeType": "application/json",
                                "thinkingConfig": {"thinkingLevel": "minimal"},
                            },
                        },
                    )
            except httpx.TimeoutException as exc:
                raise TransientFailure("The model API timed out.", "model_failed") from exc
            except httpx.TransportError as exc:
                raise TransientFailure("The model API could not be reached.", "model_failed") from exc
            if response.status_code >= 400:
                raise _model_status(response.status_code)
            try:
                return _text_from_gemma(response.json())
            except ValueError as exc:
                raise ModelError("The model API returned an unreadable response.", "model_failed") from exc

        return retry(once)
