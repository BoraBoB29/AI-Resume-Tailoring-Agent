"""Shared Mistral transport configuration and transient-error retries."""

import os

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential


DEFAULT_TIMEOUT_MS = 180000
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1


def env_int(name, default, minimum=1):
    try:
        return max(int(os.getenv(name, default)), minimum)
    except (TypeError, ValueError):
        return default


def is_retryable_error(error):
    if isinstance(
        error,
        (
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.ConnectTimeout,
            httpx.PoolTimeout,
            httpx.ConnectError,
            httpx.RemoteProtocolError,
        ),
    ):
        return True

    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code is None:
        status_code = getattr(error, "status_code", None)

    return status_code == 429 or (
        isinstance(status_code, int) and status_code >= 500
    )


def complete_with_retries(client, request):
    attempts = env_int(
        "MISTRAL_MAX_RETRIES",
        DEFAULT_MAX_RETRIES,
        minimum=0,
    ) + 1

    @retry(
        retry=retry_if_exception(is_retryable_error),
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(
            multiplier=env_int(
                "MISTRAL_RETRY_BACKOFF_SECONDS",
                DEFAULT_BACKOFF_SECONDS,
            ),
            min=1,
            max=8,
        ),
        reraise=True,
    )
    def complete():
        return client.chat.complete(**request)

    return complete()
