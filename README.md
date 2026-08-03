# 미션 개요

# 수행 내역

# Study
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
    def __init__(self, id, type, date, amount, category, memo=None, tags=None):
        self.id = id
        self.type = type
        self.date = date
        self.amount = amount
        self.category = category
        self.memo = memo
        self.tags = tags if tags is not None else []
    def __repr__(self):
        return f"Transaction(id={self.id!r}, type={self.type!r}, ...)"
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