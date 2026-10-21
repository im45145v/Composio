"""Model adapters. The vendor is selected with MODEL_PROVIDER."""

from __future__ import annotations

from typing import Protocol

import httpx

from app.research.errors import ModelError, TransientFailure, retry


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
