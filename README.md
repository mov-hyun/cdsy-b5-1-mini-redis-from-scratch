# Mini Redis from Scratch

Python의 내장 Key-Value 컬렉션에 의존하지 않고 핵심 자료구조를 직접 구현하는 CLI 기반 Mini Redis 프로젝트입니다.

> 현재 상태: 자료구조 3종과 기본 String 명령 6개를 구현했습니다. LRU 추적·메모리 제한과 TTL 만료 처리는 다음 단계에서 연결합니다.

## 목표

- 체이닝 방식 해시맵과 직접 설계한 해시 함수 구현
- 이중 연결 리스트와 해시맵을 결합한 O(1) LRU 추적
- 최소 힙을 이용한 TTL 만료 관리
- 메모리 제한과 LRU 자동 퇴출 구현
- Redis 스타일 CLI와 오류 메시지 제공

## 명령어

| 분류 | 명령어 |
| --- | --- |
| String | `SET`, `GET`, `DEL`, `EXISTS`, `DBSIZE`, `KEYS` |
| Memory (구현 예정) | `CONFIG SET maxmemory`, `INFO memory` |
| TTL (구현 예정) | `EXPIRE`, `TTL` |
| CLI | `exit`, `quit` |

## 실행 환경

- Python 3.8 이상
- 외부 런타임 의존성 없음

```powershell
python main.py
```

종료하려면 `exit` 또는 `quit`을 입력합니다.

```text
mini-redis> SET name "Alice Smith"
OK
mini-redis> GET name
"Alice Smith"
mini-redis> DEL name
(integer) 1
mini-redis> GET name
(nil)
```

명령어는 대소문자를 구분하지 않으며 키는 구분합니다. 큰따옴표로 공백이
포함된 값과 빈 문자열을 입력할 수 있습니다. `KEYS`는 패턴 인자를 받지 않습니다.

## 테스트

```powershell
python -m unittest discover -s tests -v
```

## 프로젝트 구조

```text
.
|-- mini_redis/
|   |-- __init__.py
|   |-- cli.py
|   |-- database.py
|   |-- hash_map.py
|   |-- linked_list.py
|   `-- min_heap.py
|-- tests/
|   |-- test_database.py
|   |-- test_hash_map.py
|   |-- test_linked_list.py
|   |-- test_min_heap.py
|   `-- test_project_structure.py
|-- main.py
|-- requirements.txt
`-- README.md
```

## 설계 원칙

- `dict`, `set`, `collections`로 핵심 저장소를 대체하지 않습니다.
- 해시맵은 체이닝으로 충돌을 해결하고 로드 팩터가 0.75를 초과하면 버킷을 두 배로 확장합니다.
- LRU 목록의 삽입, 삭제, 이동은 모두 O(1)로 처리합니다.
- TTL 힙은 `(expire_at, key)` 형태의 항목을 다루며 오래된 항목은 lazy deletion으로 정리할 예정입니다.
- 메모리 사용량은 `len(key.encode("utf-8")) + len(value.encode("utf-8"))`의 합으로 계산합니다.
- 만료, 명시적 삭제, LRU 퇴출은 데이터, LRU, TTL, 메모리 통계를 일관되게 갱신합니다.

## 구현 순서

1. [완료] 이중 연결 리스트와 단위 테스트
2. [완료] 체이닝 해시맵, 리사이징과 단위 테스트
3. [완료] 최소 힙과 단위 테스트
4. [완료] 기본 String 명령 (LRU·TTL 연동은 5~6단계)
5. 메모리 제한과 LRU 퇴출
6. TTL과 lazy deletion
7. CLI 오류 처리와 통합 테스트
