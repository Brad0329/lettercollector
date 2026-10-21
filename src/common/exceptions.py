"""Custom exceptions for LetterCollector."""
from enum import Enum


class CursiveErrorKind(str, Enum):
    """Classification of errors occurring during cursive script fetching/processing."""
    NETWORK = "network"        # Connection failure, timeout, HTTP error
    BAD_RESPONSE = "bad_response"  # Unexpected HTML or changed site structure
    NO_RESULTS = "no_results"      # Search performed successfully but no cursive scripts found
    VALIDATION = "validation"      # Invalid input parameter (e.g. not a single Chinese character)


class CursiveException(Exception):
    """Domain exception for LetterCollector."""

    def __init__(self, kind: CursiveErrorKind, message: str):
        super().__init__(message)
        self.kind = kind
        self.message = message

    def __str__(self) -> str:
        if self.kind == CursiveErrorKind.NETWORK:
            return f"초서를 받지 못했습니다 (네트워크 오류: {self.message})"
        elif self.kind == CursiveErrorKind.BAD_RESPONSE:
            return f"초서 검색 결과를 해석하지 못했습니다 (사이트 구조 변경 가능성: {self.message})"
        elif self.kind == CursiveErrorKind.NO_RESULTS:
            return f"초서 결과가 없습니다: {self.message}"
        elif self.kind == CursiveErrorKind.VALIDATION:
            return f"입력값 오류: {self.message}"
        return f"초서 처리 오류 ({self.kind.value}): {self.message}"
