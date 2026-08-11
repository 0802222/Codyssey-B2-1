"""
CLI 출력 전담 모듈.

app.py의 run_* 함수는 서비스 호출과 입력 흐름만 담당하고,
결과를 화면에 어떻게 보여줄지는 이 모듈의 print_* 함수가 담당한다.
"""

from budget_app.core.models import Budget, Transaction


def _format_transaction_line(tx: Transaction) -> str:
    memo = tx.memo or ""
    return f"{tx.id} | {tx.date} | {tx.type:<7} | {tx.category} | {tx.amount:,} | {memo}"


def print_transactions(transactions: list[Transaction], empty_message: str | None = None) -> None:
    if not transactions and empty_message:
        print(empty_message)
        return
    for tx in transactions:
        print(_format_transaction_line(tx))


def print_add_result(tx: Transaction) -> None:
    print(f"[저장 완료] id={tx.id}")


def print_summary(result: dict, top: int) -> None:
    if not result["has_data"]:
        print(f"[데이터 없음] {result['month']}에 해당하는 거래가 없습니다.")
        return

    print(f"총 수입: {result['total_income']}원")
    print(f"총 지출: {result['total_expense']}원")
    print(f"잔액: {result['balance']}원")

    budget = result["budget"]
    if budget is not None:
        print(f"예산: {budget['amount']}원 (사용률 {budget['usage_rate']:.1f}%)")
        if budget["over_budget"]:
            print("[경고] 예산을 초과했습니다!")

    print(f"\n지출 Category TOP {top}")
    for i, (category, amount) in enumerate(result["top_categories"], start=1):
        print(f"{i}) {category} {amount}원")


def print_budget_set_result(budget: Budget) -> None:
    print(f"[저장 완료] {budget.month} 예산 {budget.amount}원")


def print_category_add_result(name: str) -> None:
    print(f"[저장 완료] category={name}")


def print_category_list(names: list[str]) -> None:
    for name in names:
        print(f"- {name}")


def print_category_remove_result(name: str) -> None:
    print(f"[삭제 완료] category={name}")


def print_category_rename_result(old_name: str, new_name: str) -> None:
    print(f"[이름 변경 완료] {old_name} -> {new_name}")


def print_update_result(tx: Transaction) -> None:
    print(f"[수정 완료] id={tx.id}")


def print_delete_result(tx_id: str) -> None:
    print(f"[삭제 완료] id={tx_id}")
