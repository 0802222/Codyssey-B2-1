# 나만의 용돈 기입장 (Budget App)

## 미션 개요

Python 표준 라이브러리만으로 만든 `콘솔 가계부 프로그램`입니다. 
- 거래 추가/조회/검색/수정/삭제
- 월별 요약
- 예산 관리
- 카테고리 관리
- CSV import/export 기능
    (데이터는 프로그램 종료
후에도 JSONL 파일로 영구 저장)

## 실행 방법

```bash
python -m budget_app <command> [options]
```

- Python 3.10 이상, 외부 라이브러리 없이 표준 라이브러리만 사용
- 모든 명령은 `--help`로 사용법 확인 (예: `python -m budget_app add --help`)
- `--data-dir <path>` 옵션으로 데이터 저장 폴더 변경 가능 (기본값: `./data`)
- `add`, `category add`는 대화형 입력(`input()`)을 사용하고, 나머지 명령(`list`, `search`,
  `summary`, `budget set`, `category list/remove/rename`, `update`, `delete`, `import`,
  `export`)은 옵션 인자 방식 사용

## 저장 파일 위치 및 형식

기본 저장 폴더는 `./data`이며 아래 3개의 JSONL 파일로 분리 저장된다.
(파일이 없으면 최초
저장 시 자동 생성된다.)

| 파일 | 내용 | 스키마 |
|---|---|---|
| `transactions.jsonl` | 거래 내역 | `id, type(income/expense), date(YYYY-MM-DD), amount(양수 정수), category, memo(선택), tags(선택, 리스트)` |
| `categories.jsonl` | 카테고리 목록 | `name` |
| `budgets.jsonl` | 월별 예산 | `month(YYYY-MM), amount(정수)` |

카테고리 파일이 비어 있는 상태에서 `add`를 실행하면, 등록되지 않은 카테고리 입력 시 그 자리에서
바로 등록할지(`y`) 재입력할지(`n`)를 대화형으로 안내합니다. `category add`로 미리 등록해 두는
방식도 그대로 지원합니다.

**초기 실행 / 재실행 시나리오**: `./data`(또는 `--data-dir`로 지정한 폴더)와 3개 JSONL 파일은
처음 저장이 일어나는 시점에 자동 생성됩니다(파일이 없다고 오류를 내지 않습니다). 이후
프로그램을 재실행해도 같은 `--data-dir`을 가리키는 한 이전에 저장한 거래/카테고리/예산이
그대로 유지됩니다 — 별도의 초기화나 마이그레이션 절차가 필요 없습니다.

`update`/`delete`/`category remove`/`category rename`처럼 파일 전체를 다시 쓰는 작업은 임시
파일에 먼저 쓴 뒤 `os.replace`로 원자적 교체하여, 쓰기 도중 오류가 나도 원본 파일이 손상되지
않도록 합니다.

# 시연
```bash
# apt install
sudo apt-get update -y
sudo apt-get install -y git nano python3 python3-venv

# git clone
git clone https://github.com/0802222/Codyssey-B2-1 ~/Codyssey-B2-1

# script 실행
cd ~/Codyssey-B2-1
chmod +x scripts/demo.sh
./scripts/demo.sh
```
## 주요 명령어 예시

### 거래 추가 (add, 대화형)
```bash
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000012
```

### 거래 목록 (list)
```bash
$ python -m budget_app list --limit 3
TX-000012 | 2024-01-15 | expense | food | 15,000 | 점심
```

### 거래 검색 (search)
```bash
$ python -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food --type expense --q 점심 --tag meal
```

### 월별 요약 (summary)
```bash
$ python -m budget_app summary --month 2024-01 --top 3
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
예산: 500000원 (사용률 43.0%)

지출 Category TOP 3
1) rent 150000원
```

### 예산 설정/조회 (budget)
```bash
$ python -m budget_app budget set --month 2024-01 --amount 500000
[저장 완료] 2024-01 예산 500000원
```
설정된 예산은 `summary` 실행 시 사용률·초과 경고와 함께 조회됩니다.

`budget set --amount`는 `validate_amount`에서 0 이하 금액을 거부하므로, 정상 흐름에서
예산 금액은 항상 양수만 저장됩니다("무제한 예산"이라는 개념 자체가 없습니다). `summarize()`의
`(total_expense / budget.amount * 100) if budget.amount else 0`은 0으로 나누기를 막는 방어
코드일 뿐, 실제 CLI로는 도달할 일이 없습니다. 예산 관리를 아예 안 하려면 `budget set` 자체를
하지 않으면 됩니다 — `summary`는 예산이 설정되지 않은 달에는 예산 관련 줄을 아예 출력하지
않습니다.

### 카테고리 관리 (category)
```bash
$ python -m budget_app category add
카테고리명: food
[저장 완료] category=food

$ python -m budget_app category list
- food

$ python -m budget_app category remove --name food   # 사용 중이면 CategoryInUseError로 거부
$ python -m budget_app category rename --old-name food --new-name meal   # 보너스: 이름 변경(거래에도 반영)
```

카테고리 삭제 정책은 요구사항의 "삭제를 막거나 대체 카테고리를 요구" 중 **차단(막기)** 을
선택했습니다 — 사용 중인 카테고리는 `CategoryInUseError`로 삭제 자체가 거부됩니다. 다른
카테고리로 옮기고 싶다면 해당 거래들을 `update --category`로 먼저 옮기거나, 카테고리 자체를
없애지 않고 `category rename`으로 이름만 바꾸면 됩니다.

### 거래 수정 (update) — 옵션 기반으로 고정
요구사항의 "옵션 기반 / 대화형 기반" 중 **옵션 기반**으로 고정했습니다. `--id`는 필수이며,
나머지 필드는 값을 준 것만 수정됩니다.
```bash
$ python -m budget_app update --id TX-000012 --amount 20000 --memo 저녁
[수정 완료] id=TX-000012
```

### 거래 삭제 (delete)
```bash
$ python -m budget_app delete --id TX-000012
[삭제 완료] id=TX-000012
```
존재하지 않는 id는 `NotFoundError`로 처리되어 `[오류]/[힌트]` 메시지를 출력합니다.

### CSV import/export
```bash
$ python -m budget_app export --out export.csv --month 2024-01
[완료] export.csv (12 records)

$ python -m budget_app import --from import.csv
[완료] imported=5, skipped=0
```
`export`는 `--month` 또는 `--from`/`--to` 중 하나 이상을 반드시 지정해야 합니다.

CSV 스키마(고정, UTF-8, 헤더 포함):

| column | required | 설명 |
|---|---|---|
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(,) 구분 문자열 |

`import`는 CSV 전체를 먼저 읽어 각 행을 검증하고, 유효한 행만 메모리에 모은 뒤 **한 번에
원자적으로**(임시 파일 작성 후 `os.replace`) 반영합니다. 검증에 실패한 행은 건너뛰고
(`skipped`) 카운트만 늘어날 뿐 등록되지 않으며, 쓰기 단계 자체가 실패하는 경우(디스크 오류 등)
에도 원자적 교체 덕분에 `transactions.jsonl`은 import 이전 상태 그대로 유지됩니다 — 일부 행만
반영된 채 남는 상황이 생기지 않습니다.

## 오류 처리 규약

- 모든 예외는 `AppError`(및 하위 클래스 `ValidationError`/`NotFoundError`/`DuplicateError`/
  `CategoryInUseError`)로 표현되며, 스택트레이스 대신 `[오류] 원인` / `[힌트] 해결 방법` 두 줄만
  출력합니다.
- 정상 종료 시 exit code `0`, `AppError` 발생 시 `1`, `Ctrl+C`로 입력을 중단한 경우 관례적인
  SIGINT 종료 코드인 `130`을 반환합니다(`sub/decorators.py`의 `handle_errors`).
- 셸에서 종료 코드는 명령 실행 직후 `echo $?`로 확인할 수 있습니다.
  ```bash
  $ python -m budget_app delete --id TX-999999
  [오류] id=TX-999999 거래를 찾을 수 없습니다.
  [힌트] list로 존재하는 id를 확인하세요.
  $ echo $?
  1
  ```

### 공통 관심사 데코레이터 적용 위치 (`sub/decorators.py`)

| 데코레이터 | 적용 대상 | 역할 |
|---|---|---|
| `@handle_errors` | `__main__.py`의 `main()` (진입점 1곳) | `AppError`/`KeyboardInterrupt`를 잡아 스택트레이스 없이 출력하고 exit code 결정 |
| `@log_call` | `TransactionService.add/delete/update`, `import_batch` | 호출 시작/종료를 stderr에 로그 |
| `@measure_time` | `TransactionService.list_transactions/search/import_batch` | 실행 시간을 stderr에 로그 |

## 수행 내역

- 도메인 모델(Transaction/Category/Budget) 및 예외 클래스 설계
- argparse 기반 CLI, 4계층 구조(cli → core ← sub) 구현
- 파일 기반 저장소(JSONL, 제너레이터 스트리밍, 원자적 재작성) 구현
- 10대 필수 기능(add/list/search/summary/budget/category/update/delete/import/export) 구현 및 수동 검증
- 보너스 과제(백업/반복 내역/테이블 정렬)는 이번 범위에서 구현하지 않음

# Study
## 디렉토리 분리
의존성 관점에서 CLI, 핵심 로직, 하위 구현 분리
```text
cli  →  core  ←  sub
```

- cli: argparse, 사용자 입력/출력, 프로그램 실행 흐름만 담당
- core: Transaction, 서비스, 유스케이스, 핵심 규칙 담당
- sub: 파일 시스템·외부 API·저장소 등 세부 구현 담당
- 루트 __main__.py: python -m project 실행 시 CLI를 호출하는 진입점
- 루트 __init__.py: 비워 두거나 외부에 공개할 최소 API만 정의

### 계층별 핵심 진입점

| 계층 | 파일 | 핵심 함수/클래스 |
|---|---|---|
| cli | `cli/app.py` | `run_add/run_list/run_search/run_summary/run_budget_set/run_category_*/run_update/run_delete` |
| cli | `cli/flow.py` | `print_transactions/print_summary/print_*_result` (출력 전담) |
| core | `core/models.py` | `Transaction/Category/Budget` — **데이터만** 표현, 검증·저장 로직 없음 |
| core | `core/services.py` | `TransactionService/CategoryService/BudgetService/SummaryService` — **검증·계산·비즈니스 규칙** 담당, models를 조립해 repository에 위임 |
| core | `core/repository.py` | `read_transactions(제너레이터)/append_transaction/rewrite_all_*` — 파일 I/O만 담당 |
| sub | `sub/validators.py` | `validate_date/validate_amount/...` |
| sub | `sub/decorators.py` | `handle_errors/log_call/measure_time` |
| sub | `sub/io_csv.py` | `import_csv/export_csv` |

즉 **models는 순수 데이터, services는 검증과 비즈니스 로직, repository는 파일 I/O**라는
책임 경계를 명시적으로 나눴습니다 — 예를 들어 카테고리 존재 검증은 `CategoryService.exists`가
하지, `Category` 모델이나 `repository.read_categories`는 데이터를 읽고 표현만 할 뿐 검증하지
않습니다.


## `__main__.py`
### 1. 실행 흐름
`handle_errors`가 `main` 위에 붙는 순간, python 내부적으로는 이렇게 실행 된다.
```python
main = handle_errors(main)
```

즉, 원래의 `main` 함수는 `handle_errors안의` `wrapper`로 덮어씌워진다.
그래서 나중에 `if __name__ == "__main__": main()` 을 호출하면, 실제로 실행되는 건 `wrapper()` 이다.

`wrapper()` 가 실행되면:
1. `try` 블록 안에서 `func(*args, **kwargs)`를 호출 — 여기서 `func`는 원래의 `main`(진짜 로직)이다. 지금은 인자가 없으니 그냥 `main()`이 호출되는 것과 같다.

2. `main()` 내부에서 `parser.parse_args() → run_add(args)` 같은 실제 로직이 실행된다.

3. 정상적으로 끝나면 `return func(...)`이 그대로 반환되고, `wrapper`도 끝난다.

4. 로직 중간에 `AppError`(혹은 그 자식 클래스인 ValidationError, NotFoundError 등)가 발생하면, 그 예외가 `run_add` → `main` → `wrapper`까지 타고 올라와서 `except AppError as e` 블록에서 잡힌다.

5. 잡히면 스택트레이스는 절대 출력되지 않고, `[오류] ...` / `[힌트] ...` 두 줄만 출력한 뒤 `sys.exit(1)`로 비정상 종료한다.


<br>
이 구조가 필요한 이유:

과제 요구사항이 `스택트레이스 금지`, `원인 + 힌트 출력`, `정상 = 0, 오류 != 0 종료` 인데, 이 로직을 `run_add` 등 명령어 함수마다 각각 `try/except` 로 써주면 코드가 중복되기 때문에, 

대신 진입점인 `main()` 딱 한곳에만 `@handle_errors` 를 붙여주면, 공통관심사(예외처리)가 분리되어 `main()` 안에서 호출되는 모든 함수 (예: run_add 등) 어디서든 `AppError` 가 발생해도 예외가 호출 스택을 따라 올라와 결국 `wrapper` 의 `except` 에서 한번에 잡힌다.

### 2. @functools.wraps가 붙어 있는 이유
```python
@functools.wraps(func)
def wrapper(*args, **kwargs):
```
데코레이터 없이 그냥 `wrapper` 를 반환하면, `main.__name__`이 "`wrapper`"로, `main.__doc__`도 사라져 버린다. (디버깅/문서화 시 원래 함수 정보가 유실 된다.)

`functools.wraps(func)`를 붙이면 `wrapper` 가 원래함수(func, 여기서는 main)의 `이름`, `docstring`, `메타데이터` 를 그대로 복사해서 갖고 있게 된다. 

필수는 아니지만 관례처럼 데코레이터 작성 시 항상 붙이는 코드라고 한다.

### 3. *args, **kwargs 가 뭐고, 왜 필요한지?
`*args`, `**kwargs`는 인자를 몇개 받을 지 모를때, 다받아주는 문법이다.
- `*args` : 인자를 몇 개 주든 전부 튜플로 모아라
    ```python
    def func(*args):
    print(args)

    func(1, 2, 3)        # args = (1, 2, 3)
    func("a")            # args = ("a",)
    func()               # args = ()
    ```
- `**kwargs` : key=value 형태로 주는 인자를 전부 딕셔너리로 모아라
    ```python
    def func(**kwargs):
    print(kwargs)

    func(name="홍길동", age=30)     # kwargs = {"name": "초롱", "age": 32}
    func()                        # kwargs = {}
    ```

### 그럼 인자1, 인자2로 받으면 안되는지?
만약 데코레이터에 이렇게 고정해서 썼다면,
```python
def wrapper(a, b):
    return func(a, b)
```
이 데코레이터는 정확히 인자 2개를 받는 함수에만 쓸 수 있다.
`main()` 처럼 인자가 0개인 함수에 붙이면 에러가 나고, `run_add(args)`처럼 1개만 받는 함수에도 에러가 난다.

*args, **kwargs로 쓰면 데코레이터가 원본 함수의 인자 개수/이름을 몰라도 그대로 다 받아서 그대로 다 넘겨줄 수 있습니다. 그래서 `@handle_errors`를 인자 없는 `main()`에도, 인자 1개인 `run_add(args)`에도, 인자 여러 개인 다른 함수에도 똑같은 코드로 재사용할 수 있다.

```python
@handle_errors
def main():
    ...
```
`main()`은 인자가 없으므로, 호출 시 `wrapper()`가 실행되고 내부적으로 `args = (), kwargs = {}`가 됩니다. 빈 값이라도 `func(*args, **kwargs)` → `func()`로 정상 호출된다.

지금 코드에서는 `*args`, `**kwargs`가 비어있는 채로 그냥 통과되지만, 나중에 다른 함수에 재사용할 상황을 대비한 범용 설계라고 이해하면 된다.    

### 4. `argparse` 란?
`--help` 문구를 직접 작성할 필요가 없이, `ArgumentParser` 와 `add_argument`에 준 정보를 바탕으로 알아서 도움말을 만들어준다.
- `dest` : `--from` 은 파이썬 예약어 `from` 과 충돌하므로, `dest="date_from"` / `dest="import_from"` 처럼 실제 저장될 변수명을 따로 지정한다. 접근은 `args.date_from` 으로 한다.
- `metavar` : `--help` 로 출력시 `--month MONTH` 대신 `--month YYYY-MM` 처럼 사용자가 입력해야할 형식을 직접 보여주기 위한 힌트다.
- `choices` : `--type` 처럼 값이 정해진 옵션은 `chocies = ["income", "expense"]` 로 지정하면 잘못된 값 입력 시 `argparse` 가 자동으로 오류를 내준다. (직접 검증 코드를 쓰지않아도 된다.)
- sub command : `budget set`, `category add/list/remove` 처럼 명령 안에 명령이 있는 구조에는 `add_subparsers`를 한번 더 사용한다.

```bash
$ python -m budget_app list --help
usage: budget_app list [-h] [--limit LIMIT]

options:
  -h, --help     show this help message and exit
  --limit LIMIT  출력할 최대 개수 (기본값: 10)
```


## `models.py`
### 1. `dataclass` 란?
`__init__`, `__repr__`, `__eq__` 를 자동으로 만들어 준다.

장점
- 코드량 감소, 가독성 증가
- 실수 방지(필드 하나 놓쳐서 `__eq__` 가 틀리는 일이 없음)

적용 전
```python
class Transaction:
    # __init__ : 객체 새성시 자동으로 실행되며 필드값을 초기화한다.
    def __init__(self, id, type, date, amount, category, memo=None, tags=None):
        self.id = id
        self.type = type
        self.date = date
        self.amount = amount
        self.category = category
        self.memo = memo
        self.tags = tags if tags is not None else []
    
    # __repr__ : 객체를 사람이 읽을 수 있는 문자열로 표현해주는 메서드 이다.
    # 이게 없다면 콘솔에서 print(tx)를 했을 때 메모리주소만 찍혀서 디버깅 할 때 아무정보를 못얻는다.
    def __repr__(self):
        return f"Transaction(id={self.id!r}, type={self.type!r}, ...)"

    # 두 객체를 == 로 비교할 때 어떤 기준으로 같다고 판단할지 정의 하는 메서드    
    def __eq__(self, other):
        return (self.id, self.type, ...) == (other.id, other.type, ...)
```

적용 후 (간단해짐)
```python
@dataclass
class Transaction:
    id: str
    type: str       # income | expense
    data: str      # YYYY-MM-DD
    amount: int
    category: str
    memo: Optional[str] = None
    tags: list[str] = field(default_factory = list)
```

### 1.1 dataclass(frozen=True)
dataclass에 frozen=True 옵션을 주면, 생성 뒤 필드 재할당을 막아 읽기전용처럼 동작하게 한다.

다만 Python에서 완전한 불변성을 보장하는 것은 아니고, 내부에 list나 dict 같은 가변 객체가 있으면 그 내부 내용은 바뀔 수 있다.

반대로, transaction 자체가 처리 과정에서 status, retry_count, completed_at 등을 계속 갱신해야 하는 객체라면 frozen=True 는 맞지 않다.

이런 경우 아래중 하나가 더 깔끔하다.
- Transaction은 불변 명세로 유지하고, 실행 상태는 별도 TransactionResult 또는 TransactionState 로 관리
- 상태 변경마다 dataclasses.replace()로 새 Transaction 생성
- 애초에 상태를 가진 서비스/엔티티로 설계하고 frozen 을 적용하지 않음
<br>

### 2. `field` 와 `default_factory의` 의미

- `field` 는 `dataclasses` 모듈이 제공하는 함수로, 기본값을 어떻게 만들지에 대해 세부설정을 줄 대 사용한다.
- `default_factory` 는 기본값을 생성하는 함수(팩토리)를 받는 파라미터 이다.

- 사용 예시
```python
    # 올바른 사용 예
    tags: list[str] = field(default_factory = list)

    # 틀린 사용 예 (X)
    tags: list[str] = []
```

`Python` 에서 `[]`, `{}`, `list()` 처럼 변경 가능한 `mutable` 객체를 기본값으로 직접 쓰면, 모든 인스턴스가 그 리스트를 공유하는 버그가 생긴다.

그래서 이 문제를 방지하기 위해 `field(default_factory = list)` 를 쓰면 "기본값이 필요할 때 마다 `list()`를 새로 호출해서 만들어라" 는 뜻이 되어, 인스턴스마다 독립된 빈 리스트가 생성된다.    

<br>

### 3. `tags` 가 `Optional` 처럼 동작하는 이유
```python
# 값이 str 이거나 None일 수 있음, 기본값은 None
memo: Optional[str] == None

# 문자열 리스트만 허용, 기본값은 빈 리스트 []
tags: list[str] == feild(default_factory = list)
```

앱을 실행해보면 `memo` 와 `tags` 모두 값을 입력하지않아도 에러없이 동작한다.
- `memo` 는 `Optional`이기 때문에 값의 입력이 선택사항이다.
- `tags` 는 `Optional` 이 아닌데 왜 입력하지않아도 에러가 발생하지 않을까?

그 이유는 `default_factory` 가 기본값을 빈 리스트 `[]` 로 지정해줘서 
사용자가 `tags`를 안넘겨도 에러 없이 `Transaction(...)`이 생성되고, 자동으로 `tags=[]` 가 채워진다.

<br>

### 4. `typing` 모듈의 여러 타입들

`typing` 은 타입 힌트를 더 정교하게 표현하기 위한 표준 라이브러리이다. 주로 사용하는 함수들은 아래와 같다.

| 이름 | 의미 |
|-----|-----|
| `Optional`[X] | X 또는 None (= X \| None과 동일)| 
| `list`[X], `dict`[K, V]| 파이썬 3.9+ 부터는 typing.List 대신 그냥 list, dict 써도 됨| 
| `Iterator`[X]| X를 하나씩 내놓는 이터레이터(제너레이터 반환형에 흔히 씀)| 
| `Union`[X, Y]| X 또는 Y (여러 타입 허용)| 
| `Any`| 아무 타입이나 허용(타입 체크 포기)| 
| `Callable`[[Args], Return]| 함수 타입 (데코레이터 힌트에 씀)| 

## repository.py
### 1. 타입 힌트(return type annotation)
```python
def read_transactions(path: str) -> Iterator[Transaction]:
```
path(문자열)을 받아서 Iterator[Transaction]을 반환한다는 계약을 명시한다.

### 2. 제너레이터
파일 전체를 리스트로 만들어 메모리에 올리지 않고, "한 줄 읽고 -> 하나 내주고 -> 다음 요청 오면 또 한 줄" 이 반복된다.

`yield` 는 함수를 제너레이터로 만들어주는 키워드 이다.

`return` 은 값을 반환 하고 함수를 완전히 끝내지만,
`yield` 는 값을 하나 내주고 함수 실행을 그자리에서 멈춘 채 대기한다. 다음에 또 값이 필요하면(예. for문에서 다음 반복) 멈췄던 지점부터 다시 이어서 실행한다.

### 3. `**data` 의 의미
`*(단일 별표)` 는 리스트/튜플을 위치 인자로 풀고,
`**(이중 별표)` 는 딕셔너리를 키워드 인자(key=value)로 풀어준다.

`**data` 는 딕셔너리인 data(json.loads(line)으로 만들어짐)를 키워드 인자로 풀어서(unpacking) 전달하는 문법이다.

즉, 아래 두 코드는 완전히 같다.
```python
Transacntion(**data)

# 위와 동일
Transaction(id="TX-001", type="expense", data="2026-08-01", amount=15000, category="food")
```


### 왜 내부 저장 포맷으로 JSONL을 선택했나 (JSONL vs CSV)

요구사항은 JSONL/CSV 중 택1을 허용하지만, 이 프로젝트는 **내부 저장은 JSONL, 외부 교환은
CSV**로 용도를 분리했습니다. 이유는 다음과 같습니다.

| 관점 | JSONL | CSV |
|---|---|---|
| 스트리밍 처리 | 한 줄 = 완결된 레코드라서 `for line in f: json.loads(line)`으로 한 줄씩 즉시 파싱 가능 (`repository.py`의 `read_transactions`가 제너레이터로 구현) | `csv.DictReader`도 스트리밍은 되지만, 필드 안에 쉼표/줄바꿈이 섞이면 quoting 규칙에 의존해야 해서 파싱이 더 민감함 |
| 스키마 유연성 | 레코드마다 독립적인 JSON 객체라 `tags`처럼 리스트 값이나 선택적 필드(`memo`)를 자연스럽게 표현. 필드 추가 시 기존 줄은 그대로 두고 새 줄부터 필드를 늘려도 파싱이 깨지지 않음 | 모든 행이 같은 컬럼 수/순서를 강제해야 함. `tags`처럼 다중값 필드는 쉼표 구분 문자열로 다시 인코딩해야 해서 표현력이 떨어짐(현재 CSV export에서 `",".join(tx.tags)`로 우회) |
| 수정 시 원자성 | 레코드 단위 append(`append_transaction`)가 가능해 `add`는 파일 전체를 안 건드리고 한 줄만 추가. `update`/`delete`만 전체 재작성(`rewrite_all_transactions` + `os.replace`) | CSV도 append 자체는 가능하지만, 헤더 한 줄을 전체 파일이 공유하기 때문에 사실상 JSONL과 비슷한 이점은 없고 quoting 이슈만 추가됨 |
| 사람이 읽기/디버깅 | 한 줄에 레코드 하나라 `tail -f`, `grep`으로 특정 거래를 바로 찾기 쉬움 | 표 형태로 한눈에 보기는 더 좋지만, 필드에 쉼표/줄바꿈이 있으면 눈으로 읽기 어려움 |
| 도구 호환성 | 표준 라이브러리 `json`만으로 충분 | 엑셀/시트 도구와의 호환성이 높음 → **import/export 스키마를 CSV로 고정**한 이유 |

결론: **거래가 계속 추가·수정·삭제되는 내부 저장소**에는 레코드 단위 append와 스트리밍 파싱이
유리한 JSONL을 쓰고, **다른 도구(엑셀 등)와 주고받는 경계**에는 범용성이 높은 CSV를 그대로
유지해 요구사항의 CSV 스키마(위 표)를 만족시켰습니다.

## 대용량(10만 건 이상) 시나리오 병목 분석

`transactions.jsonl`이 10만 건 이상으로 커졌을 때 실제로 느려지는 지점과 개선 방향입니다.

| 병목 지점 | 코드 근거 | 문제 | 개선 방안 |
|---|---|---|---|
| **`add`할 때마다 ID 채번을 위해 전체 스캔** | `TransactionService._next_id()`가 매번 `read_transactions(self.path)`를 끝까지 순회하며 최대 번호를 계산 | 거래 1건 추가에 O(n) — 10만 건째 거래를 추가할 때 이전 99,999건을 전부 다시 읽음. `add`를 반복할수록 전체적으로 O(n²) | 마지막으로 발급한 ID를 별도 카운터 파일(예: `data/.next_id`)이나 `budgets.jsonl`처럼 작은 메타 파일에 캐시해 O(1)로 다음 ID를 계산 |
| **`list`/`search`의 전체 정렬** | `list_transactions`/`search`가 제너레이터로 읽어들인 뒤 `sorted(...)`로 전체를 메모리에 올려 정렬 | `list --limit 10`처럼 일부만 필요해도 10만 건을 전부 메모리에 올리고 정렬(O(n log n)) | 날짜 역순이 대부분의 목적이라면, append 시 항상 날짜 오름차순을 유지하도록 삽입 위치를 관리하거나, 파일을 월별로 분할해 최근 파일부터 역순으로 읽는 방식으로 실질적인 스캔 범위를 줄일 수 있음 |
| **`update`/`delete`/`category rename`의 전체 재작성** | `rewrite_all_transactions`가 매번 전체 리스트를 새 임시 파일에 다시 씀 | 거래 1건만 수정해도 나머지 99,999건을 통째로 다시 씀 (O(n) I/O) | 원자성을 위해 "전체 재작성"은 유지하되, 빈도가 낮은 명령(update/delete)에서만 감수하는 트레이드오프로 명시. 빈도가 훨씬 높은 `add`는 이미 append 전용이라 이 비용에서 제외되어 있음 |
| **`summary`의 월별 집계** | `SummaryService.summarize`가 매번 `transactions.jsonl` 전체를 순회하며 해당 월만 필터링 | 특정 월 요약 1번에도 전체 파일을 스캔(O(n)) | 저장을 월별 파일(`transactions-2024-01.jsonl` 등)로 분할하면 해당 월 파일만 읽어 스캔 범위를 줄일 수 있음 |

**정리**: 현재 구조에서 가장 급한 병목은 `_next_id()`의 전체 스캔입니다(모든 `add` 호출마다
발생하며 누적 시 O(n²)). `update`/`delete`의 전체 재작성은 원자성 확보를 위한 의도된 트레이드
오프이고 호출 빈도도 낮아 상대적으로 덜 급합니다. 이번 범위에서는 분석까지만 진행하고 실제
개선 구현(카운터 파일, 월별 파일 분할 등)은 하지 않았습니다.


# 동료평가 시 나눈 이야기들
### 거래 삭제 후 거래번호는 공석으로 남는가?
[확인]
- 거래를 1~4까지 생성한다.
- 거래 2와 4를 삭제 한다.
- 거래 신규 생성 시 삭제됐던 4의 번호를 재사용해 4로 생성되었다.

[원인]
- 기존 next_id()는 transactions.jsonl에 남아있는 거래의 최댓값 + 1 로 채번된다.

[개선]
- transactions.seq에 마지막으로 발급된 번호를 별도로 영속시켜 add / import_batch 가 이 카운터만 증가시키도록 변경한다.
- 삭제는 카운터에 영향을 주지 않으므로, 삭제된 번호는 다시 발급되지 않는다.
- 카운터 파일이 없는 기존 데이터는 최초 1회 transactions.jsonl의 최댓값으로 초기화되어 하위 호환된다.