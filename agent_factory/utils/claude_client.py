"""Thin wrapper around the Anthropic SDK with prompt caching, streaming,
retries, and a no-API-key mock mode for graceful degradation."""
from __future__ import annotations

import os
import time
from typing import Iterator, Optional

try:  # The SDK is optional at import time so mock mode works without it.
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore


# Most capable model for this complex meta-AI task.
DEFAULT_MODEL = "claude-opus-4-8"

# Adaptive thinking is the recommended mode on Opus 4.8.
DEFAULT_THINKING = {"type": "adaptive"}
DEFAULT_EFFORT = "high"
DEFAULT_MAX_TOKENS = 16000


class ClaudeClient:
    """Wraps message creation with prompt caching on the (large) system prompt.

    If no API key is available (or the SDK is not installed), the client runs
    in *mock mode* and returns deterministic placeholder text so the whole
    pipeline remains runnable for demos and tests.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_retries: int = 4,
        mock: Optional[bool] = None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if mock is None:
            # Auto-detect: mock when no key or no SDK.
            self.mock = resolved_key is None or anthropic is None
        else:
            self.mock = mock

        self.client = None
        if not self.mock:
            if anthropic is None:
                raise RuntimeError(
                    "The 'anthropic' package is not installed. Install it or run "
                    "in mock mode (unset ANTHROPIC_API_KEY)."
                )
            self.client = anthropic.Anthropic(api_key=resolved_key)

    # ------------------------------------------------------------------

    def _system_blocks(self, system_prompt: str, use_cache: bool) -> list[dict]:
        block: dict = {"type": "text", "text": system_prompt}
        if use_cache:
            # Cache the large, stable orchestrator system prompt so every
            # phase call after the first reads it at ~0.1x cost.
            block["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
        return [block]

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        use_cache: bool = True,
    ) -> str:
        """Return the full response text for a single phase call."""
        if self.mock:
            return _mock_response(user_message)

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                # Stream under the hood for robustness on long generations,
                # then collect the final message.
                with self.client.messages.stream(  # type: ignore[union-attr]
                    model=self.model,
                    max_tokens=self.max_tokens,
                    thinking=DEFAULT_THINKING,
                    output_config={"effort": DEFAULT_EFFORT},
                    system=self._system_blocks(system_prompt, use_cache),
                    messages=[{"role": "user", "content": user_message}],
                ) as stream:
                    final = stream.get_final_message()
                return _text_of(final)
            except Exception as exc:  # noqa: BLE001 - retry on transient errors
                last_exc = exc
                if not _is_retryable(exc) or attempt == self.max_retries - 1:
                    raise
                time.sleep(min(2 ** attempt, 30))
        assert last_exc is not None
        raise last_exc

    def stream(
        self,
        system_prompt: str,
        user_message: str,
        use_cache: bool = True,
    ) -> Iterator[str]:
        """Yield text chunks as they arrive."""
        if self.mock:
            for chunk in _mock_response(user_message).split(". "):
                yield chunk + ". "
            return

        with self.client.messages.stream(  # type: ignore[union-attr]
            model=self.model,
            max_tokens=self.max_tokens,
            thinking=DEFAULT_THINKING,
            output_config={"effort": DEFAULT_EFFORT},
            system=self._system_blocks(system_prompt, use_cache),
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text in stream.text_stream:
                yield text


# ---- helpers ----------------------------------------------------------


def _text_of(message) -> str:
    parts = []
    for block in getattr(message, "content", []):
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def _is_retryable(exc: Exception) -> bool:
    if anthropic is None:
        return False
    retryable = (
        getattr(anthropic, "RateLimitError", ()),
        getattr(anthropic, "InternalServerError", ()),
        getattr(anthropic, "APIConnectionError", ()),
        getattr(anthropic, "APITimeoutError", ()),
        getattr(anthropic, "OverloadedError", ()),
    )
    retryable = tuple(t for t in retryable if isinstance(t, type))
    return isinstance(exc, retryable)


def _mock_response(user_message: str) -> str:
    """Deterministic placeholder so the pipeline runs without an API key."""
    head = user_message.strip().splitlines()[0] if user_message.strip() else "phase"
    head = head[:120]
    return (
        f"[MOCK OUTPUT] No ANTHROPIC_API_KEY set, so this is placeholder content.\n\n"
        f"Phase instruction received:\n> {head}\n\n"
        "In a live run, the Agent Factory Orchestrator (claude-opus-4-8) would "
        "produce a detailed, production-ready response here, building on all "
        "prior phases passed in as context."
    )
