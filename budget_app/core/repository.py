"""
파일 I/O 전담 계층.

"어떻게 읽고 쓰는지"만 알고 "왜/언제 읽고 쓰는지"는 모른다(그건 services.py의 책임).

- read_transactions: 제너레이터로 한 줄씩 읽어 파일 전체를 메모리에 올리지 않는다.
- append_transaction: 새 거래 한 건을 파일 끝에 추가한다 (add에서 사용).
- rewrite_all: 전체 리스트를 임시 파일에 쓴 뒤 os.replace로 원자적 교체한다 (update/delete에서 사용).
"""

import json
import os
import tempfile
from typing import Iterator

from budget_app.core.models import Budget, Category, Transaction


# ── Transaction ──────────────────────────────────────────────

def read_transactions(path: str) -> Iterator[Transaction]:
    """transactions 파일을 한 줄씩 읽어 Transaction으로 변환해 yield한다 (스트리밍)."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            yield Transaction(**data)


def append_transaction(path: str, tx: Transaction) -> None:
    """거래 한 건을 파일 끝에 추가한다."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")


def rewrite_all_transactions(path: str, transactions: list[Transaction]) -> None:
    """전체 거래 리스트를 임시 파일에 쓴 뒤 원자적으로 교체한다 (update/delete용)."""
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_", suffix=".jsonl")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for tx in transactions:
                f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


# ── Category ─────────────────────────────────────────────────

def read_categories(path: str) -> list[Category]:
    """카테고리는 보통 개수가 적으므로 리스트로 바로 반환한다."""
    if not os.path.exists(path):
        return []
    result = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            result.append(Category(**data))
    return result


def rewrite_all_categories(path: str, categories: list[Category]) -> None:
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_", suffix=".jsonl")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for c in categories:
            f.write(json.dumps({"name": c.name}, ensure_ascii=False) + "\n")
    os.replace(tmp_path, path)


# ── Budget ───────────────────────────────────────────────────

def read_budgets(path: str) -> list[Budget]:
    if not os.path.exists(path):
        return []
    result = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            result.append(Budget(**data))
    return result


def rewrite_all_budgets(path: str, budgets: list[Budget]) -> None:
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_", suffix=".jsonl")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for b in budgets:
            f.write(json.dumps({"month": b.month, "amount": b.amount}, ensure_ascii=False) + "\n")
    os.replace(tmp_path, path)
