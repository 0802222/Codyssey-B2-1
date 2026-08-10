"""
데이터 모델 정의.

여기 있는 클래스들은 "데이터가 어떤 필드로 구성되는가"만 표현한다.
저장/검증/계산 로직은 절대 넣지 않는다 (그건 repository.py / services.py의 역할).
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    """거래 내역 한 건."""

    id: str
    type: str            # "income" | "expense"
    date: str             # "YYYY-MM-DD"
    amount: int
    category: str
    memo: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """저장(JSONL 직렬화)을 위해 dict로 변환."""
        return {
            "id": self.id,
            "type": self.type,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": self.tags,
        }


@dataclass
class Category:
    """카테고리 한 건."""

    name: str


@dataclass
class Budget:
    """월별 예산 한 건."""

    month: str    # "YYYY-MM"
    amount: int
