#!/usr/bin/env bash
# 미션 요구사항 "2. 최종 결과물"의 10가지 기능을 실제로 실행하고 입출력을 그대로 보여주는
# 자동화 데모 스크립트
#
#   1) 거래 추가(add)        6) 예산 관리(budget set)
#   2) 거래 목록 조회(list)  7) 카테고리 관리(category add/list/rename/remove)
#   3) 거래 검색(search)     8) 거래 수정(update)
#   4) 월별 요약(summary)    9) 거래 삭제(delete)
#   5) (4번에 포함)          10) CSV export/import
#
# 실행 결과를 이용자용 스토리(거래를 쌓고 -> 확인하고 -> 고치고 -> 내보내고 -> 다시 들여오는)로
# 이어서, 각 명령의 실제 stdout과 exit code를 그대로 노출한다.
#
# 사용법: ./scripts/demo.sh   (레포 루트 어디서 실행해도 동작)

set -uo pipefail  # set -e는 의도적으로 사용하지 않음: 7번에서 exit code 1을 직접 시연해야 함

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DATA_DIR="./demo_data"
rm -rf "$DATA_DIR"
APP=(python3 -m budget_app --data-dir "$DATA_DIR")

section() {
  echo
  echo "======================================================================"
  echo "$1"
  echo "======================================================================"
}

# 옵션 기반 명령 실행 + 실제 exit code 출력
run() {
  echo "\$ ${*}"
  "$@"
  echo "[종료 코드] $?"
}

# category add처럼 프롬프트 1개짜리 대화형 명령
run_interactive_1() {
  local cmd_label="$1" prompt_value="$2"; shift 2
  echo "\$ ${*}"
  echo "  (입력) $prompt_value"
  printf '%s\n' "$prompt_value" | "$@"
  echo "[종료 코드] $?"
}

# add처럼 프롬프트 여러 개인 대화형 명령. stdin은 $'...\n...' 형식으로 받는다.
# stdout을 그대로 보여주면서, 생성된 거래 id(TX-xxxxxx)를 표준출력 마지막 줄로 돌려준다.
run_add() {
  local stdin_data="$1"
  # 화면 출력은 전부 stderr로: 이 함수는 TX_XXX=$(run_add ...) 형태로 호출되어
  # stdout(마지막 줄의 생성 id)만 변수에 캡처되어야 하기 때문.
  {
    echo "\$ ${APP[*]} add"
    echo "$stdin_data" | sed 's/^/  (입력) /'
  } >&2
  local output
  output=$(printf '%s' "$stdin_data" | "${APP[@]}" add)
  local code=$?
  { echo "$output"; echo "[종료 코드] $code"; } >&2
  echo "$output" | grep -oE 'TX-[0-9]+' | tail -1
}

section "0. 준비: 실행 환경 확인"
run "${APP[@]}" list --help

# ── 7) 카테고리 관리 (add) — add 기능의 선행 조건 ──────────────────────────
section "1/10. 카테고리 관리 - category add (거래 추가 전 선행 등록)"
run_interactive_1 "category add" "salary" "${APP[@]}" category add
run_interactive_1 "category add" "food" "${APP[@]}" category add
run_interactive_1 "category add" "temp" "${APP[@]}" category add

# ── 1) 거래 추가 (add, 대화형) ────────────────────────────────────────────
section "2/10. 거래 추가 - add (대화형: 날짜/타입/카테고리/금액/메모/태그)"
TX_INCOME=$(run_add $'2024-01-05\nincome\nsalary\n3000000\n1월 급여\n\n')
TX_FOOD_1=$(run_add $'2024-01-10\nexpense\nfood\n15000\n점심\nmeal\n')
TX_FOOD_2=$(run_add $'2024-01-15\nexpense\nfood\n45000\n저녁 회식\nmeal,dinner\n')
echo
echo "(생성된 id) TX_INCOME=$TX_INCOME, TX_FOOD_1=$TX_FOOD_1, TX_FOOD_2=$TX_FOOD_2"

# ── 2) 거래 목록 조회 (list) ─────────────────────────────────────────────
section "3/10. 거래 목록 조회 - list"
run "${APP[@]}" list --limit 10

# ── 3) 거래 검색 (search) ────────────────────────────────────────────────
section "4/10. 거래 검색 - search (기간/카테고리/타입/키워드/태그 조합)"
run "${APP[@]}" search --from 2024-01-01 --to 2024-01-31 --category food --type expense --q 점심 --tag meal
echo
echo "-- 검색 결과 없음 케이스 --"
run "${APP[@]}" search --category salary --type expense

# ── 6) 예산 관리 (budget set) ────────────────────────────────────────────
section "5/10. 예산 관리 - budget set (일부러 초과되도록 낮게 설정)"
run "${APP[@]}" budget set --month 2024-01 --amount 50000

# ── 4) 월별 요약 (summary) — 예산 사용률/초과 경고까지 함께 확인 ──────────
section "6/10. 월별 요약 - summary (총수입/총지출/잔액/예산 사용률/초과 경고/카테고리 TOP)"
run "${APP[@]}" summary --month 2024-01 --top 3

# ── 7) 카테고리 관리 (list/rename/remove) ────────────────────────────────
section "7/10. 카테고리 관리 - category list / rename / remove"
run "${APP[@]}" category list
echo
echo "-- 이름 변경: food -> diet (연결된 거래에도 반영) --"
run "${APP[@]}" category rename --old-name food --new-name diet
echo
echo "-- 사용 중이 아닌 카테고리 삭제: 성공 케이스 --"
run "${APP[@]}" category remove --name temp
echo
echo "-- 사용 중인 카테고리 삭제 시도: 차단 케이스 (CategoryInUseError, exit code 1) --"
run "${APP[@]}" category remove --name diet

# ── 8) 거래 수정 (update, 옵션 기반) ─────────────────────────────────────
section "8/10. 거래 수정 - update (--id 필수, 나머지는 준 값만 수정)"
run "${APP[@]}" update --id "$TX_FOOD_1" --amount 20000 --memo 저녁
run "${APP[@]}" list --limit 10

# ── 9) 거래 삭제 (delete) ────────────────────────────────────────────────
section "9/10. 거래 삭제 - delete"
run "${APP[@]}" delete --id "$TX_FOOD_2"
echo
echo "-- 존재하지 않는 id 삭제 시도: 오류 케이스 (NotFoundError, exit code 1) --"
run "${APP[@]}" delete --id TX-999999

# ── 10) CSV export / import ──────────────────────────────────────────────
section "10/10. CSV 내보내기(export) / 들여오기(import)"
EXPORT_PATH="./demo_export.csv"
run "${APP[@]}" export --out "$EXPORT_PATH" --month 2024-01
echo
echo "-- 내보낸 CSV 내용 --"
cat "$EXPORT_PATH"

IMPORT_PATH="./demo_import.csv"
cat > "$IMPORT_PATH" <<CSV
date,type,category,amount,memo,tags
2024-01-20,expense,diet,12000,저녁,meal
2024-13-99,expense,diet,9999,잘못된날짜,
CSV
echo
echo "-- 들여올 CSV 내용 (2번째 행은 의도적으로 date가 잘못됨 -> skip 되어야 함) --"
cat "$IMPORT_PATH"
echo
run "${APP[@]}" import --from "$IMPORT_PATH"
run "${APP[@]}" list --limit 10

section "완료: 10가지 기능 실행 로그 끝"
echo "데모용 데이터/파일 위치: $DATA_DIR/, $EXPORT_PATH, $IMPORT_PATH"
echo "정리하려면: rm -rf $DATA_DIR $EXPORT_PATH $IMPORT_PATH"
