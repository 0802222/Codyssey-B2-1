# 진입점 : argparse 파싱 -> 서비스 호출
# 역할 1. 명령어 체계 정의 (argparse로 add/list/search/summary/budget/category/update/delete/import/export 서브커맨드 등록)
# 역할 2. 파싱된 인자를 서비스 계층에 전달 (실제 로직은 여기서 처리하지 않음)
# 역할 3. 프로그램 실행/종료 관리 (sys.exit())

import sys
import argparse
from decorators import handle_errors
from services import TransactionService, BudgetService, CategoryService

def build_parser():
    parser = argparse.ArgumentParser(
        prog="budget_app", 
        description="나만의 용돈 기입장"
    )
    
    parser.add_argument(
        "--data-dir", 
        default="./data", 
        help="데이터 저장 폴더"
    )
    
    sub = parser.add_subparsers(
        dest="command", 
        required=True, 
        help="실행할 명령"
    )
    
    # add: 거래 추가
    sub.add_parser(
        "add", 
        help="거래를 추가합니다. (대화형: 날짜/타입/카테고리/금액/메모/태그 순차 입력)"
    )

    # list: 거래 목록 
    list_parser = sub.add_parser(
        "list", 
        help="거래 목록을 최신순으로 조회합니다."
    )
    
    list_parser.add_argument(
        "--limit", 
        type=int, 
        default=10, 
        help="출력할 최대 거래 건수(기본 값: 10"
    )

    # search: 거래 검색
    search_parser = sub.add_parser(
        "search",
        help="조건(기간/카테고리/타입/메모/태그)에 맞는 거래를 검색합니다."
    )
    
    search_parser.add_argument(
        "--from",
        dest="date_from",
        metavar="YYYY-MM-DD",
        help="검색 시작 날짜(포함)"
    )
    
    search_parser.add_argument(
        "--to",
        dest="date_to",
        metavar="YYYY-MM-DD",
        help="검색 종료 날짜(포함)"
    )
    
    search_parser.add_argument(
        "--category",
        help="검색할 카테고리명 (예: food, transport, rent ..)")
    
    search_parser.add_argument(
        "--type",
        help="거래 타입(income | expense)"
    )
    
    search_parser.add_argument(
        "--q",
        metavar="KEYWORD",
        help="메모에 포함된 키워드로 검색"
    )
    
    search_parser.add_argument(
        "--tag",
        help="특정 태그가 포함된 거래만 검색"
    )

    # summary: 월별 요약
    summary_parser = sub.add_parser(
        "summary",
        help="특정 월의 총수입/총지출/잔액과 카테고리별 지출 TOP 3를 출력합니다."
    )
    summary_parser.add_argument(
        "--month",
        required=True,
        metavar="YYYY-MM",
        help="요약할 대상 월 (예: 2026-08)"
    )
    
    summary_parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="지출 상위 카태고리 출력 개수(기본값: 3)"
    )

    # budget: 예산 설정/조회
    budget_parser = sub.add_parser(
        "budget",
        help="월별 예산을 설정하거나 조회합니다."
    )
    
    budget_sub = budget_parser.add_subparsers(
        dest="budget_command",
        required=True,
        help="budget 하위 명령"
    )
    
    set_parser = budget_sub.add_parser(
        "set",
        help="특정 월의 예산 금액을 설정합니다."
    )
    
    set_parser.add_argument(
        "--month",
        required=True,
        metavar="YYYY-MM",
        help="예산을 설정할 월 (예: 2026-09)"
    )
    
    set_parser.add_argument(
        "--amount",
        type=int,
        required=True,
        help="설정할 예산 금액 (양수 정수, 원 단위)"
    )
    
    # category: 카테고리 관리
    category_parser = sub.add_parser(
        "category",
        help="카테고리를 추가/조회/삭제합니다"
    )
    
    category_sub = category_parser.add_subparsers(
        dest="category_command", 
        required=True, 
        help="category 하위 명령"
    )

    category_sub.add_parser(
        "add",
        help="새 카테고리를 추가합니다 (대화형: 카테고리명 입력)"
    )
    
    category_sub.add_parser(
        "list",
        help="등록된 카테고리 목록을 출력합니다"
    )
    
    category_remove_parser = category_sub.add_parser(
        "remove",
        help="카테고리를 삭제합니다 (사용 중인 카테고리는 삭제 제한/대체 필요)"
    )
    
    category_remove_parser.add_argument(
        "--name",
        required=True,
        help="삭제할 카테고리명"
    )

    # update: 거래 수정
    update_parser = sub.add_parser(
        "update",
        help="id로 특정 거래의 필드를 수정합니다 (없는 id는 오류 처리)"
    )
    
    update_parser.add_argument(
        "--id",
        required=True,
        help="수정할 거래의 id (예: TX-000012)"
    )
    
    update_parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="변경할 날짜 (미입력 시 기존 값 유지)"
    )
    
    update_parser.add_argument(
        "--type",
        choices=["income", "expense"],
        help="변경할 타입 (income 또는 expense)"
    )
    
    update_parser.add_argument(
        "--category",
        help="변경할 카테고리 (등록된 카테고리만 가능)"
    )
    
    update_parser.add_argument(
        "--amount",
        type=int,
        help="변경할 금액 (양수 정수)"
    )
    
    update_parser.add_argument(
        "--memo",
        help="변경할 메모"
    )
    
    update_parser.add_argument(
        "--tags",
        help="변경할 태그 (쉼표로 구분, 예: meal,lunch)"
    )

    # delete: 거래 삭제
    delete_parser = sub.add_parser(
        "delete",
        help="id로 특정 거래를 삭제합니다 (없는 id는 오류 처리)"
    )
    
    delete_parser.add_argument(
        "--id",
        required=True,
        help="삭제할 거래의 id (예: TX-000012)"
    )

    # import: CSV 가져오기
    import_parser = sub.add_parser(
        "import",
        help="CSV 파일에서 거래 내역을 일괄 등록합니다"
    )
    
    import_parser.add_argument(
        "--from",
        dest="import_from",
        required=True,
        metavar="CSV_PATH",
        help="가져올 CSV 파일 경로"
    )

    # export: CSV 내보내기
    export_parser = sub.add_parser(
        "export",
        help="조건에 맞는 거래를 CSV 파일로 내보냅니다"
    )
    
    export_parser.add_argument(
        "--out",
        required=True,
        metavar="CSV_PATH",
        help="저장할 CSV 파일 경로"
    )
    
    export_parser.add_argument(
        "--month",
        metavar="YYYY-MM",
        help="내보낼 대상 월 (--from/--to 대신 사용 가능)"
    )
    
    export_parser.add_argument(
        "--from",
        dest="date_from",
        metavar="YYYY-MM-DD",
        help="내보낼 시작 날짜 (--month 대신 --from/--to 조합 사용)"
    )
    
    export_parser.add_argument(
        "--to",
        dest="date_to",
        metavar="YYYY-MM-DD",
        help="내보낼 종료 날짜"
    )

    return parser
   

@handle_errors
def main():
    parser = build_parser()
    args = parser.parse_args()
    
    if args.command == "add" :
        run_add(args)
    elif args.command == "list" :
        run_list(args)
    elif args.command == "search":
        run_search(args)
    elif args.command == "summary":
        run_summary(args)
    elif args.command == "budget":
        run_budget(args)
    elif args.command == "category":
        run_category(args)
    elif args.command == "update":
        run_update(args)
    elif args.command == "delete":
        run_delete(args)
    elif args.command == "import":
        run_import(args)
    elif args.command == "export":
        run_export(args)
    sys.exit(0) # 정상 종료
    
if __name__ == "__main__":
    main()