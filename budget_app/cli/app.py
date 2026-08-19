"""
CLI 계층 — 대화형 input()/출력(print)만 담당한다.

검증/저장 로직은 절대 여기 넣지 않는다. services.py를 호출하고,
services.py가 던지는 AppError는 여기서 잡지 않고 그대로 위로 올려보내
__main__.py의 handle_errors 데코레이터가 최종 처리하게 한다.
"""

from budget_app.cli import flow
from budget_app.core.exceptions import ValidationError
from budget_app.core.services import BudgetService, CategoryService, SummaryService, TransactionService
from budget_app.sub.validators import parse_tags, validate_amount, validate_category_name, validate_date, validate_type


def _prompt_valid(prompt: str, validate_fn) -> str:
    """검증에 실패하면 원인+힌트를 출력하고 계속 재입력을 요구한다."""
    while True:
        value = input(prompt)
        try:
            validate_fn(value)
            return value
        except ValidationError as e:
            print(f"[오류] {e.message}")
            if e.hint:
                print(f"[힌트] {e.hint}")


def run_add(args) -> None:
    service = TransactionService(args.data_dir)
    category_service = CategoryService(args.data_dir)

    date = _prompt_valid("날짜(YYYY-MM-DD): ", validate_date)
    type_ = _prompt_valid("타입(income/expense): ", validate_type)
    category = _prompt_valid("카테고리: ", validate_category_name)
    
    while not category_service.exists(category):
        print(f"[오류] 등록되지 않은 카테고리입니다: {category}")
        while True:
            choice = input("카테고리를 등록하시겠습니까? (y/n): ").strip().lower()
            if choice == "y":
                category_service.add(category)
                print(f"[저장 완료] category={category}")
                break
            elif choice == "n":
                print("[힌트] category add로 먼저 등록하거나 등록된 카테고리를 입력하세요.")
                break
            print("[오류] y 또는 n만 입력하세요.")
        if category_service.exists(category):
            break
        category = _prompt_valid("카테고리: ", validate_category_name)
        
    amount = _prompt_valid("금액(양수): ", validate_amount)
    memo = input("메모(선택): ") or None
    tags_raw = input("태그(쉼표로 구분, 없으면 엔터): ")
    tags = parse_tags(tags_raw)

    tx = service.add(date, type_, category, amount, memo, tags)
    flow.print_add_result(tx)


def run_list(args) -> None:
    service = TransactionService(args.data_dir)
    flow.print_transactions(service.list_transactions(limit=args.limit), empty_message="[아직 등록된 거래가 없습니다.]")


def run_search(args) -> None:
    service = TransactionService(args.data_dir)
    results = service.search(
        date_from=args.date_from,
        date_to=args.date_to,
        category=args.category,
        type_=args.type,
        query=args.q,
        tag=args.tag,
    )
    flow.print_transactions(results, empty_message="[검색 결과 없음]")


def run_summary(args) -> None:
    service = SummaryService(args.data_dir)
    result = service.summarize(args.month, top=args.top)
    flow.print_summary(result, top=args.top)


def run_budget_set(args) -> None:
    service = BudgetService(args.data_dir)
    budget = service.set(args.month, args.amount_str)
    flow.print_budget_set_result(budget)


def run_category_add(args) -> None:
    service = CategoryService(args.data_dir)
    name = _prompt_valid("카테고리명: ", validate_category_name)
    service.add(name)
    flow.print_category_add_result(name)


def run_category_list(args) -> None:
    service = CategoryService(args.data_dir)
    flow.print_category_list(service.list_categories())


def run_category_remove(args) -> None:
    service = CategoryService(args.data_dir)
    transactions_path = f"{args.data_dir}/transactions.jsonl"
    service.remove(args.name, transactions_path)
    flow.print_category_remove_result(args.name)

def run_category_rename(args) -> None:
    service = CategoryService(args.data_dir)
    transactions_path = f"{args.data_dir}/transactions.jsonl"
    old_name = validate_category_name(args.old_name)
    new_name = validate_category_name(args.new_name)
    service.rename(old_name, new_name, transactions_path)
    flow.print_category_rename_result(old_name, new_name)

def run_update(args) -> None:
    service = TransactionService(args.data_dir)
    tx = service.update(
        tx_id=args.id,
        date=args.date,
        type_=args.type,
        category=args.category,
        amount_str=str(args.amount) if args.amount is not None else None,
        memo=args.memo,
        tags=parse_tags(args.tags) if args.tags is not None else None,
    )
    flow.print_update_result(tx)


def run_delete(args) -> None:
    service = TransactionService(args.data_dir)
    service.delete(args.id)
    flow.print_delete_result(args.id)
