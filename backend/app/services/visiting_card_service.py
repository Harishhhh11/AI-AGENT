"""Two-sided visiting-card extraction and merge foundation.

OCR/vision providers are intentionally injected so this service works with any
provider that supports Telugu, English, or mixed-language cards.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable
from typing import Any


class VisitingCardService:
    REQUIRED_SIDE = "side_1"
    OPTIONAL_SIDE = "side_2"

    MULTI_VALUE_FIELDS = {
        "phones",
        "emails",
        "websites",
        "social_links",
        "services",
        "other_details",
    }

    def __init__(self, extractor: Callable[[bytes, str], dict[str, Any]]):
        self.extractor = extractor

    def extract(
        self,
        side_1: bytes,
        side_1_content_type: str,
        side_2: bytes | None = None,
        side_2_content_type: str | None = None,
    ) -> dict[str, Any]:
        if not side_1:
            raise ValueError("side_1 is required")
        if side_2 and not side_2_content_type:
            raise ValueError("side_2_content_type is required when side_2 is provided")

        first = self.extractor(side_1, side_1_content_type) or {}
        second = (
            self.extractor(side_2, side_2_content_type or "application/octet-stream") or {}
            if side_2
            else {}
        )
        return self.merge(first, second, side_2_processed=bool(side_2))

    def merge(
        self,
        side_1: dict[str, Any],
        side_2: dict[str, Any] | None = None,
        *,
        side_2_processed: bool | None = None,
    ) -> dict[str, Any]:
        side_2 = side_2 or {}
        result: dict[str, Any] = {}
        keys = set(side_1) | set(side_2)

        for key in keys:
            left = side_1.get(key)
            right = side_2.get(key)
            if key in self.MULTI_VALUE_FIELDS or isinstance(left, (list, tuple, set)) or isinstance(right, (list, tuple, set)):
                result[key] = self._unique([*self._as_list(left), *self._as_list(right)])
            else:
                result[key] = left if self._has_value(left) else right

        for key in self.MULTI_VALUE_FIELDS:
            result.setdefault(key, [])

        result["metadata"] = {
            "side_1_processed": True,
            "side_2_processed": bool(side_2_processed if side_2_processed is not None else side_2),
        }
        return result

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]

    @staticmethod
    def _has_value(value: Any) -> bool:
        return value is not None and (not isinstance(value, str) or bool(value.strip()))

    def _unique(self, values: Iterable[Any]) -> list[Any]:
        result: list[Any] = []
        seen: set[str] = set()
        for value in values:
            if not self._has_value(value):
                continue
            text = str(value).strip()
            normalized = self._normalize(text)
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(text)
        return result

    @staticmethod
    def _normalize(value: str) -> str:
        value = unicodedata.normalize("NFKC", value).casefold()
        value = re.sub(r"[^\w\u0C00-\u0C7F]+", "", value, flags=re.UNICODE)
        return value
