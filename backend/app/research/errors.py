"""Failures the pipeline can record without echoing provider payloads."""

from __future__ import annotations


class ResearchError(Exception):
    def __init__(self, message: str, code: str, *, transient: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.transient = transient


class UnsafeURL(ResearchError):
    def __init__(self, message: str, code: str = "unsafe_url") -> None:
        super().__init__(message, code)


class InvalidAppName(ResearchError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "invalid_app")


class SearchError(ResearchError):
    pass


class ReaderError(ResearchError):
    pass


class ModelError(ResearchError):
    pass


class InsufficientEvidence(ResearchError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "insufficient_evidence")


class CredentialsInOutput(ResearchError):
    def __init__(self) -> None:
        super().__init__(
            "The model output included credential material, so no guide was saved.",
            "credentials_in_output",
        )


class RunInProgress(Exception):
    def __init__(self, run_id: str) -> None:
        super().__init__(run_id)
        self.run_id = run_id


class TransientFailure(ResearchError):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message, code, transient=True)


def retry(action, attempts: int = 2):
    last: ResearchError | None = None
    for attempt in range(attempts):
        try:
            return action()
        except ResearchError as exc:
            last = exc
            if not exc.transient or attempt + 1 == attempts:
                raise
    if last is not None:
        raise last
    raise ResearchError("The request failed.", "internal_error")
