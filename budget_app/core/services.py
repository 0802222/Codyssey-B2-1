"""
비즈니스 로직 전담 계층.

__main__.py(CLI)와 repository.py(파일 I/O) 사이의 중간 계층.
"검증하고, 계산하고, 규칙을 적용한 뒤 repository를 호출한다"가 이 계층의 책임이다.
"""

import os
from collections import defaultdict
from typing import Iterator, Optional

from budget_app.core.exceptions import CategoryInUseError, DuplicateError, NotFoundError, ValidationError
from budget_app.core.models import Budget, Category, Transaction
from budget_app.core.repository import (
    append_transaction,
    read_budgets,
    read_categories,
    read_transactions,
    rewrite_all_budgets,
    rewrite_all_categories,
    rewrite_all_transactions,
)
from budget_app.sub.validators import validate_amount, validate_category_name, validate_date, validate_month, validate_type


class CategoryService:
    def __init__(self, data_dir: str) -> None:
        self.path = os.path.join(data_dir, "categories.jsonl")

    def list_categories(self) -> list[str]:
        return [c.name for c in read_categories(self.path)]

    def exists(self, name: str) -> bool:
        return name in self.list_categories()

    def add(self, name: str) -> None:
        name = validate_category_name(name)
        names = self.list_categories()
        if name in names:
            raise DuplicateError(f"이미 존재하는 카테고리입니다: {name}")
        categories = read_categories(self.path)
        categories.append(Category(name=name))
        rewrite_all_categories(self.path, categories)

    def remove(self, name: str, transactions_path: str) -> None:
        if not self.exists(name):
            raise NotFoundError(f"존재하지 않는 카테고리입니다: {name}")
        in_use = any(tx.category == name for tx in read_transactions(transactions_path))
        if in_use:
            raise CategoryInUseError(
                f"'{name}' 카테고리를 사용 중인 거래가 있어 삭제할 수 없습니다.",
                hint="해당 거래를 먼저 update로 다른 카테고리로 변경하세요.",
            )
        categories = [c for c in read_categories(self.path) if c.name != name]
        rewrite_all_categories(self.path, categories)

    def rename(self, old_name: str, new_name: str, transactions_path: str) -> None:
        old_name = validate_category_name(old_name)
        new_name = validate_category_name(new_name)
        if not self.exists(old_name):
            raise NotFoundError(f"존재하지 않는 카테고리입니다: {old_name}")
        if self.exists(new_name):
            raise DuplicateError(f"이미 존재하는 카테고리입니다: {new_name}")

        categories = []
        for category in read_categories(self.path):
            if category.name == old_name:
                categories.append(Category(name=new_name))
            else:
                categories.append(category)
        rewrite_all_categories(self.path, categories)

        transactions = []
        for tx in read_transactions(transactions_path):
            if tx.category == old_name:
                transactions.append(Transaction(**{**tx.to_dict(), "category": new_name}))
            else:
                transactions.append(tx)
        rewrite_all_transactions(transactions_path, transactions)


class TransactionService:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.path = os.path.join(data_dir, "transactions.jsonl")
        self.category_service = CategoryService(data_dir)

    def _next_id(self) -> str:
        max_num = 0
        for tx in read_transactions(self.path):
            num = int(tx.id.split("-")[-1])
            max_num = max(max_num, num)
        return f"TX-{max_num + 1:06d}"

    def add(
        self,
        date: str,
        type_: str,
        category: str,
        amount_str: str,
        memo: Optional[str],
        tags: list[str],
    ) -> Transaction:
        validate_date(date)
        validate_type(type_)
        category = validate_category_name(category)
        amount = validate_amount(amount_str)
        if not self.category_service.exists(category):
            raise ValidationError(
                f"등록되지 않은 카테고리입니다: {category}",
                hint="category add로 먼저 등록하세요.",
            )
        tx = Transaction(
            id=self._next_id(),
            type=type_,
            date=date,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags,
        )
        append_transaction(self.path, tx)
        return tx

    def list_transactions(self, limit: int = 10) -> list[Transaction]:
        all_tx = sorted(read_transactions(self.path), key=lambda t: t.date, reverse=True)
        return all_tx[:limit]

    def search(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        category: Optional[str] = None,
        type_: Optional[str] = None,
        query: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> list[Transaction]:
        def matches(tx: Transaction) -> bool:
            if date_from and tx.date < date_from:
                return False
            if date_to and tx.date > date_to:
                return False
            if category and tx.category != category:
                return False
            if type_ and tx.type != type_:
                return False
            if query and (not tx.memo or query not in tx.memo):
                return False
            if tag and tag not in tx.tags:
                return False
            return True

        filtered = (tx for tx in read_transactions(self.path) if matches(tx))
        return sorted(filtered, key=lambda t: (t.date, t.amount), reverse=True)

    def delete(self, tx_id: str) -> None:
        all_tx = list(read_transactions(self.path))
        filtered = [t for t in all_tx if t.id != tx_id]
        if len(filtered) == len(all_tx):
            raise NotFoundError(
                f"id={tx_id} 거래를 찾을 수 없습니다.",
                hint="list로 존재하는 id를 확인하세요.",
            )
        rewrite_all_transactions(self.path, filtered)

    def update(
        self,
        tx_id: str,
        date: Optional[str] = None,
        type_: Optional[str] = None,
        category: Optional[str] = None,
        amount_str: Optional[str] = None,
        memo: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Transaction:
        all_tx = list(read_transactions(self.path))
        target_index = next((i for i, t in enumerate(all_tx) if t.id == tx_id), None)
        if target_index is None:
            raise NotFoundError(
                f"id={tx_id} 거래를 찾을 수 없습니다.",
                hint="list로 존재하는 id를 확인하세요.",
            )

        target = all_tx[target_index]
        new_date = target.date
        new_type = target.type
        new_category = target.category
        new_amount = target.amount
        new_memo = target.memo
        new_tags = target.tags

        if date is not None:
            validate_date(date)
            new_date = date
        if type_ is not None:
            validate_type(type_)
            new_type = type_
        if category is not None:
            if not self.category_service.exists(category):
                raise ValidationError(f"등록되지 않은 카테고리입니다: {category}")
            new_category = category
        if amount_str is not None:
            new_amount = validate_amount(amount_str)
        if memo is not None:
            new_memo = memo
        if tags is not None:
            new_tags = tags

        updated = Transaction(
            id=target.id,
            type=new_type,
            date=new_date,
            amount=new_amount,
            category=new_category,
            memo=new_memo,
            tags=new_tags,
        )
        all_tx[target_index] = updated

        rewrite_all_transactions(self.path, all_tx)
        return updated


class BudgetService:
    def __init__(self, data_dir: str) -> None:
        self.path = os.path.join(data_dir, "budgets.jsonl")

    def set(self, month: str, amount_str: str) -> Budget:
        validate_month(month)
        amount = validate_amount(amount_str)
        budgets = read_budgets(self.path)
        budgets = [b for b in budgets if b.month != month]
        budget = Budget(month=month, amount=amount)
        budgets.append(budget)
        rewrite_all_budgets(self.path, budgets)
        return budget

    def get(self, month: str) -> Optional[Budget]:
        for b in read_budgets(self.path):
            if b.month == month:
                return b
        return None


class SummaryService:
    """월별 요약(수입/지출/잔액/카테고리 TOP N/예산 사용률) 계산 전담."""

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.transactions_path = os.path.join(data_dir, "transactions.jsonl")
        self.budget_service = BudgetService(data_dir)

    def summarize(self, month: str, top: int = 3) -> dict:
        validate_month(month)
        month_tx = [tx for tx in read_transactions(self.transactions_path) if tx.date.startswith(month)]

        if not month_tx:
            return {"has_data": False, "month": month}

        total_income = sum(tx.amount for tx in month_tx if tx.type == "income")
        total_expense = sum(tx.amount for tx in month_tx if tx.type == "expense")
        balance = total_income - total_expense

        category_totals: dict[str, int] = defaultdict(int)
        for tx in month_tx:
            if tx.type == "expense":
                category_totals[tx.category] += tx.amount
        top_categories = sorted(category_totals.items(), key=lambda kv: kv[1], reverse=True)[:top]

        budget = self.budget_service.get(month)
        budget_info = None
        if budget is not None:
            usage_rate = (total_expense / budget.amount * 100) if budget.amount else 0
            budget_info = {
                "amount": budget.amount,
                "usage_rate": usage_rate,
                "over_budget": total_expense > budget.amount,
            }

        return {
            "has_data": True,
            "month": month,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "top_categories": top_categories,
            "budget": budget_info,
        }
