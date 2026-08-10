"""
진입점. 실행: python -m budget_app <command> [options]

역할: argparse로 명령어 체계를 정의하고, 파싱된 인자를 알맞은 run_xxx()에 전달한다.
실제 검증/저장 로직은 여기 없다 (app.py -> services.py -> repository.py로 위임).
"""

import argparse
import sys
from budget_app.cli.app import (
    run_add,
    run_budget_set,
    run_category_add,
    run_category_list,
    run_category_remove,
    run_category_rename,
    run_search,
    run_summary,
    run_update,
    run_delete,
    run_list,
    run_search,
    run_summary,
    run_update,
)
from budget_app.sub.decorators import handle_errors
from budget_app.core.exceptions import ValidationError
from budget_app.sub.io_csv import export_csv, import_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="나만의 용돈 기입장 - 콘솔 가계부 프로그램",
    )
    parser.add_argument("--data-dir", default="./data", help="데이터 파일을 저장/조회할 폴더 (기본값: ./data)")

    sub = parser.add_subparsers(dest="command", required=True, help="실행할 명령")

    sub.add_parser("add", help="거래를 추가합니다 (대화형 입력)")

    list_p = sub.add_parser("list", help="거래 목록을 최신순으로 조회합니다")
    list_p.add_argument("--limit", type=int, default=10, help="출력할 최대 거래 건수 (기본값: 10)")

    search_p = sub.add_parser("search", help="조건에 맞는 거래를 검색합니다")
    search_p.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD", help="검색 시작 날짜")
    search_p.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD", help="검색 종료 날짜")
    search_p.add_argument("--category", help="카테고리로 필터링")
    search_p.add_argument("--type", choices=["income", "expense"], help="타입으로 필터링")
    search_p.add_argument("--q", metavar="KEYWORD", help="메모 키워드 검색")
    search_p.add_argument("--tag", help="태그로 필터링")

    summary_p = sub.add_parser("summary", help="월별 요약을 출력합니다")
    summary_p.add_argument("--month", required=True, metavar="YYYY-MM", help="요약 대상 월")
    summary_p.add_argument("--top", type=int, default=3, help="지출 상위 카테고리 개수 (기본값: 3)")

    budget_p = sub.add_parser("budget", help="월별 예산을 설정/조회합니다")
    budget_sub = budget_p.add_subparsers(dest="budget_command", required=True)
    budget_set_p = budget_sub.add_parser("set", help="월 예산을 설정합니다")
    budget_set_p.add_argument("--month", required=True, metavar="YYYY-MM")
    budget_set_p.add_argument("--amount", dest="amount_str", required=True, help="예산 금액")

    category_p = sub.add_parser("category", help="카테고리를 관리합니다")
    category_sub = category_p.add_subparsers(dest="category_command", required=True)
    category_sub.add_parser("add", help="카테고리를 추가합니다 (대화형)")
    category_sub.add_parser("list", help="카테고리 목록을 조회합니다")
    
    category_update_p = category_sub.add_parser("rename", help="카테고리 이름을 변경합니다")
    category_update_p.add_argument("--old-name", required=True)
    category_update_p.add_argument("--new-name", required=True)

    category_remove_p = category_sub.add_parser("remove", help="카테고리를 삭제합니다")
    category_remove_p.add_argument("--name", required=True)

    update_p = sub.add_parser("update", help="id로 거래를 수정합니다")
    update_p.add_argument("--id", required=True)
    update_p.add_argument("--date", metavar="YYYY-MM-DD")
    update_p.add_argument("--type", choices=["income", "expense"])
    update_p.add_argument("--category")
    update_p.add_argument("--amount", type=int)
    update_p.add_argument("--memo")
    update_p.add_argument("--tags", help="쉼표로 구분 (예: meal,lunch)")

    delete_p = sub.add_parser("delete", help="id로 거래를 삭제합니다")
    delete_p.add_argument("--id", required=True)

    import_p = sub.add_parser("import", help="CSV에서 거래를 일괄 등록합니다")
    import_p.add_argument("--from", dest="import_from", required=True, metavar="CSV_PATH")

    export_p = sub.add_parser("export", help="조건에 맞는 거래를 CSV로 내보냅니다")
    export_p.add_argument("--out", required=True, metavar="CSV_PATH")
    export_p.add_argument("--month", metavar="YYYY-MM")
    export_p.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD")
    export_p.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD")

    return parser


@handle_errors
def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "add":
        run_add(args)
    elif args.command == "list":
        run_list(args)
    elif args.command == "search":
        run_search(args)
    elif args.command == "summary":
        run_summary(args)
    elif args.command == "budget":
        if args.budget_command == "set":
            run_budget_set(args)
    elif args.command == "category":
        if args.category_command == "add":
            run_category_add(args)
        elif args.category_command == "list":
            run_category_list(args)
        elif args.category_command == "remove":
            run_category_remove(args)
        elif args.category_command == "rename":
            run_category_rename(args)
    elif args.command == "update":
        run_update(args)
    elif args.command == "delete":
        run_delete(args)
    elif args.command == "import":
        imported, skipped = import_csv(args.data_dir, args.import_from)
        print(f"[완료] imported={imported}, skipped={skipped}")
    elif args.command == "export":
        if not args.month and not (args.date_from and args.date_to):
            raise ValidationError(
                "export 조건이 필요합니다.",
                hint="--month YYYY-MM 또는 --from/--to를 함께 지정하세요.",
            )
        count = export_csv(args.data_dir, args.out, args.month, args.date_from, args.date_to)
        print(f"[완료] {args.out} ({count} records)")

    sys.exit(0)


if __name__ == "__main__":
    main()
