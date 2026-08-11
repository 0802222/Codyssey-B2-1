"""
CSV import/export 전담 모듈.

CSV 스키마 (고정):
  date(필수, YYYY-MM-DD), type(필수, income/expense), category(필수),
  amount(필수, 양수 정수), memo(선택), tags(선택, 쉼표 구분)
공통: UTF-8, 헤더 포함
"""

import csv

from budget_app.core.exceptions import ValidationError
from budget_app.core.services import TransactionService
from budget_app.sub.validators import parse_tags

CSV_FIELDS = ["date", "type", "category", "amount", "memo", "tags"]


def import_csv(data_dir: str, csv_path: str) -> tuple[int, int]:
    """CSV에서 거래를 일괄 등록한다. (imported, skipped) 건수를 반환."""
    service = TransactionService(data_dir)
    imported = 0
    skipped = 0

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                service.add(
                    date=row["date"],
                    type_=row["type"],
                    category=row["category"],
                    amount_str=row["amount"],
                    memo=row.get("memo") or None,
                    tags=parse_tags(row.get("tags") or ""),
                )
                imported += 1
            except ValidationError:
                skipped += 1

    return imported, skipped


def export_csv(data_dir: str, out_path: str, month: str | None, date_from: str | None, date_to: str | None) -> int:
    """조건에 맞는 거래를 CSV로 내보낸다. 내보낸 건수를 반환."""
    service = TransactionService(data_dir)

    if month:
        results = service.search(date_from=f"{month}-01", date_to=f"{month}-31")
    else:
        results = service.search(date_from=date_from, date_to=date_to)

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for tx in results:
            writer.writerow(
                {
                    "date": tx.date,
                    "type": tx.type,
                    "category": tx.category,
                    "amount": tx.amount,
                    "memo": tx.memo or "",
                    "tags": ",".join(tx.tags),
                }
            )

    return len(results)
