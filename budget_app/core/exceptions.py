"""
커스텀 예외 클래스 모음.

모든 예외는 AppError를 상속한다.
message: 오류 원인
hint: 해결 힌트 (없으면 None)

__main__.py의 handle_errors 데코레이터가 이 예외를 잡아서
"[오류] {message}" / "[힌트] {hint}" 형태로만 출력하고,
스택트레이스는 절대 출력하지 않는다.
"""

from typing import Optional


class AppError(Exception):
    """모든 앱 예외의 베이스 클래스."""

    def __init__(self, message: str, hint: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ValidationError(AppError):
    """입력값 검증 실패 (날짜 형식, 음수 금액, 잘못된 type 등)."""


class NotFoundError(AppError):
    """id, category, month 등 존재하지 않는 대상을 조회/수정/삭제하려 할 때."""


class DuplicateError(AppError):
    """이미 존재하는 카테고리를 다시 추가하려 할 때 등."""


class CategoryInUseError(AppError):
    """사용 중인 카테고리를 삭제하려 할 때."""
