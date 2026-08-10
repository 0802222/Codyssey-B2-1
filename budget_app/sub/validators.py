"""
입력 검증 함수 모음.

여기 함수들은 실패 시 항상 ValidationError를 던진다.
호출부(services.py, cli.py)에서 이 예외를 잡아 재입력을 요구하거나,
handle_errors 데코레이터까지 올려보내 최종 출력하게 한다.
"""

from datetime import datetime

from budget_app.core.exceptions import ValidationError

ALLOWED_TYPES = ("income", "expense")


def validate_date(date_str: str) -> str:
    """'YYYY-MM-DD' 형식인지 검증. 통과하면 그대로 반환."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(
            "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).",
            hint="예: 2024-01-15",
        )
    return date_str


def validate_month(month_str: str) -> str:
    """'YYYY-MM' 형식인지 검증."""
    try:
        datetime.strptime(month_str, "%Y-%m")
    except ValueError:
        raise ValidationError(
            "월 형식이 올바르지 않습니다 (YYYY-MM).",
            hint="예: 2024-01",
        )
    return month_str


def validate_type(type_str: str) -> str:
    """type이 income/expense 중 하나인지 검증."""
    if type_str not in ALLOWED_TYPES:
        raise ValidationError(
            f"허용되지 않은 타입입니다: {type_str}",
            hint="income 또는 expense 중 하나를 입력하세요.",
        )
    return type_str


def validate_amount(amount_str: str) -> int:
    """금액이 양의 정수인지 검증 후 int로 변환."""
    try:
        amount = int(amount_str)
    except ValueError:
        raise ValidationError(
            "금액은 숫자여야 합니다.",
            hint="예: 15000",
        )
    if amount <= 0:
        raise ValidationError(
            "금액은 0보다 큰 양수여야 합니다.",
            hint="예: 15000",
        )
    return amount


def validate_category_name(name: str) -> str:
    """카테고리명이 비어 있지 않은지 검증하고, 양끝 공백을 제거해 반환한다."""
    cleaned = name.strip()
    if not cleaned:
        raise ValidationError(
            "카테고리명은 비어 있을 수 없습니다.",
            hint="공백이 아닌 이름을 입력하세요.",
        )
    return cleaned


def parse_tags(tags_str: str) -> list[str]:
    """쉼표로 구분된 태그 문자열을 리스트로 변환. 빈 입력이면 빈 리스트."""
    if not tags_str.strip():
        return []
    return [t.strip() for t in tags_str.split(",") if t.strip()]
