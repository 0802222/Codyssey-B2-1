# 데이터 모델
# Transaction, Category, Budget(dataclass)

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Transaction:
    id: str
    type: str       # income | expense
    data: str      # YYYY-MM-DD
    amount: int
    category: str
    memo: Optional[str] = None
    tags: list[str] = field(default_factory=list)