# 공통 관심사(횡단 관심사) 함수 - 다른 함수 위에 @으로 얹어서 재사용한다.
# @log_call(호출 로그), @mesuare_time(측정 시간), @handle_errors(예외 처리)

"""
공통 관심사(횡단 관심사)를 분리한 데코레이터 모음.

- handle_errors : AppError를 잡아 "[오류]/[힌트]" 형태로만 출력, 스택트레이스 숨김, exit code 결정
- measure_time  : 함수 실행 시간을 stderr에 로그로 남김
- log_call      : 함수 호출 자체를 stderr에 로그로 남김 (선택)
"""


import functools
import sys
import time
from typing import Any, Callable, TypeVar

from budget_app.core.exceptions import AppError

F = TypeVar("F", bound=Callable[..., Any])


def handle_errors(func: F) -> F:
    """AppError를 잡아 사용자 친화적 메시지로 출력하고, 오류 시 exit code 1로 종료한다."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except AppError as e:
            print(f"[오류] {e.message}")
            if e.hint:
                print(f"[힌트] {e.hint}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n[취소] 사용자가 입력을 중단했습니다.")
            sys.exit(130)

    return wrapper  # type: ignore[return-value]


def measure_time(func: F) -> F:
    """함수 실행 시간을 측정해 stderr에 로그로 남긴다."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[LOG] {func.__name__} 실행 시간: {elapsed:.4f}초", file=sys.stderr)
        return result

    return wrapper  # type: ignore[return-value]


def log_call(func: F) -> F:
    """함수 호출과 종료를 stderr에 로그로 남긴다."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"[LOG] {func.__name__} 호출 시작", file=sys.stderr)
        result = func(*args, **kwargs)
        print(f"[LOG] {func.__name__} 호출 종료", file=sys.stderr)
        return result

    return wrapper  # type: ignore[return-value]
