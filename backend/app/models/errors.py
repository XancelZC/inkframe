"""Standard error response format.

From PRD section "API Design" — error response structure.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Machine-readable error codes."""

    PROVIDER_ERROR = "provider_error"
    RATE_LIMITED = "rate_limited"
    INVALID_JSON = "invalid_json"
    SCHEMA_VALIDATION_FAILED = "schema_validation_failed"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    BAD_REQUEST = "bad_request"
    STAGE_FAILED = "stage_failed"
    MISSING_PREREQUISITE = "missing_prerequisite"


class ErrorDetail(BaseModel):
    """Error detail object."""

    code: ErrorCode
    message: str
    details: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""

    error: ErrorDetail
