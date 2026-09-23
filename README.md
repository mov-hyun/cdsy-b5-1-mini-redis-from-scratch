# Mini Redis from Scratch

Python의 내장 Key-Value 컬렉션에 의존하지 않고 핵심 자료구조를 직접 구현하는 CLI 기반 Mini Redis 프로젝트입니다.

> 현재 상태: 필수 기능과 보너스 과제 5개를 모두 구현했습니다. 테스트 63개가 통과했으며 실행 예시와 설계 설명을 함께 제공합니다.

- [구조와 설계 이유](docs/DESIGN.md)
- [실행 예시와 재현 방법](docs/DEMO.md)
- [검증 결과와 요구사항 대응](docs/VALIDATION.md)
- [스택·큐·덱 정리 (보너스 2)](docs/STACK_QUEUE_DEQUE.md)
- [확장 논의: LFU 전환·대규모 병목·used_memory 모델](docs/DISCUSSION.md)

## 목표

- 체이닝 방식 해시맵과 직접 설계한 해시 함수 구현
- 이중 연결 리스트와 해시맵을 결합한 O(1) LRU 추적
- 최소 힙을 이용한 TTL 만료 관리
- 메모리 제한과 LRU 자동 퇴출 구현
- Redis 스타일 CLI와 오류 메시지 제공

## 확장 설계 논의 (요약)

세부 내용과 코드 예시는 [docs/DISCUSSION.md](docs/DISCUSSION.md)에 있습니다. 수치는 2026-09-23,
Windows 11 / Python 3.12에서 `MiniRedis.execute`를 직접 호출해 측정했습니다.

### 1. LRU → LFU 전환: 빈도 카운트 · 자료구조 변경 · 정책 재설계

- **빈도 카운트 추가**: 키마다 접근 횟수 `freq`를 저장하고 성공한 GET/SET마다 1씩 올린다.
  전체에서 가장 작은 빈도 `min_freq`도 함께 유지한다.
- **자료구조 변경**: 현재 `lru`(리스트 1개) + `lru_nodes`(키 → 노드)를
  `freq_lists`(빈도 → `DoublyLinkedList`) + `lfu_nodes`(키 → (노드, 빈도))로 바꾼다.
  둘 다 기존 `HashMap`, `DoublyLinkedList`를 재사용하며 정렬이나 힙 없이 모든 연산이 O(1)이다.

| 연산 | LRU (현재) | LFU (전환 후) |
| --- | --- | --- |
| 새 키 | `insert_front` | `freq_lists[1].insert_front`, `min_freq = 1` |
| 접근 성공 | `move_to_front` | 현재 리스트에서 `remove_node` → `freq_lists[f+1].insert_front`, 옛 리스트가 비고 `f == min_freq`면 `min_freq += 1` |
| 퇴출 대상 | `lru.tail` | `freq_lists[min_freq].tail` (같은 빈도 안에서는 LRU) |
| DEL/만료 | `lru.remove_node` | 해당 빈도 리스트에서 `remove_node` |

- **코드 변경 범위**: `database.py`의 `_touch`, `_set`의 퇴출 루프, `_remove_key`의 세 곳만 교체한다.
- **정책 재설계**
  - 빈도 감쇠: 옛날에 인기 있던 키가 계속 남지 않도록 일정 시간마다 빈도를 절반으로 줄인다.
  - 신규 키 보호: 새 키의 초기 빈도를 1보다 크게 줘서 넣자마자 퇴출되지 않게 한다.
  - 동점 규칙: 같은 빈도에서는 LRU로 정한다.
  - 우선순위: 만료 정리를 먼저 하고, 그래도 한도를 넘으면 LFU로 퇴출한다.
  - 기존 동작 유지: `CONFIG SET maxmemory-policy allkeys-lru|allkeys-lfu`로 고르게 하고 기본값은 LRU로 둔다.

### 2. 대규모(10만 키) 병목 식별과 완화

| 측정 (10만 키) | 결과 | 병목 원인 | 완화책 |
| --- | --- | --- | --- |
| SET 평균 / 최악 | 16.9µs / **361.8ms** | 98,304번째 키에서 로드 팩터 0.75를 넘어 버킷 131,072 → 262,144개로 한 번에 전체 리해시 | 점진적 리해시(명령마다 버킷 몇 개씩 이동), 초기 용량 지정 |
| GET 평균 | 4.4µs | 최대 체인 길이 3으로 해시 분포 양호 | 해당 없음 |
| 같은 키에 EXPIRE를 점점 짧게 10만 번 | 힙 항목 **100,000개** | lazy deletion은 루트에 올라온 무효 항목만 버림 | 힙이 유효 TTL 수의 2배를 넘으면 유효 항목만으로 재구성, 또는 키 → 힙 위치 인덱스 힙 |
| KEYS 1회 | 79.8ms | 버킷 + 키 전체 O(n) 순회 | 커서 기반 SCAN |
| 대량 동시 만료 | 명령 하나에 정리가 몰림 | `_purge_expired`가 만료된 키를 한 번에 모두 삭제 | 명령당 정리 개수 상한, 주기적 샘플링 정리 |

- **샤딩·병렬화**: `hash(key) % N`으로 N개의 `MiniRedis` 인스턴스에 나눠 담는다.
  샤드마다 해시맵·LRU·힙·`maxmemory / N`을 따로 가지므로 리해시와 정리 비용이 1/N이 되고,
  샤드별로 병렬 처리할 수 있다. LRU는 샤드 단위 근사가 되고, KEYS·DBSIZE는 모든 샤드의 결과를 합쳐야 한다.
- **I/O 제약**: 네트워크를 붙이면 입력 대기가 병목이 된다. 비동기 I/O 이벤트 루프가 소켓을 처리하고
  명령 실행은 단일 스레드에서 순서대로 하면 자료구조에 락이 필요 없다.
- **적용 순서**: 무효 힙 항목 정리 → 정리 개수 상한 → 점진적 리해시 → SCAN·샤딩.

### 3. used_memory 모델 변경: 오버헤드 포함 · 공정 비교 · 채점 영향

키 1만 개 기준으로 과제 공식 `used_memory`는 127,780바이트, `tracemalloc`으로 잰 실제 할당은
10,993,764바이트(약 **86배**)였다. 차이는 str 객체 헤더, 버킷 배열, 체인 노드,
`HashMapEntry`, LRU 노드, `lru_nodes` 맵에서 생긴다.

| 오버헤드 포함 시 항목 | 영향 | 보정 방법 |
| --- | --- | --- |
| 퇴출 시점 | 같은 `maxmemory`에서 훨씬 일찍 퇴출되고, 과제 예시(`maxmemory 30`)에서는 키 1개도 못 넣음 | 한도를 같은 모델로 환산: `effective_max = maxmemory × (1 + 평균 오버헤드 비율)` |
| 결정성 | `sys.getsizeof`, `tracemalloc` 값이 Python 버전·OS에 따라 달라짐 | 실측 대신 고정 상수 모델: `엔트리 수 × ENTRY_COST + 버킷 수 × BUCKET_COST` |
| 빈 DB 비용 | 초기 버킷만으로도 사용량이 0이 아님 | 기준선 보정: 빈 DB 값을 `baseline`으로 두고 `used_memory - baseline`으로 비교 |
| 공정 비교·채점 | 공식 기준 제출물과 used_memory·evicted_keys 수치를 직접 비교할 수 없음 | 공식 `used_memory`는 유지하고 `used_memory_overhead`를 별도 필드로 출력, 모델은 `CONFIG`로 선택(기본값 공식) |
| 테스트 | 정확한 바이트 값 검증이 환경마다 깨짐 | 공식 모델은 정확한 값으로, 오버헤드 모델은 "퇴출 후 한도 이하" 같은 불변식으로 검증 |

결론: 채점과 테스트가 공식 값에 맞춰져 있으므로 퇴출 기준인 `used_memory` 정의는 바꾸지 않고,
오버헤드는 참고 지표로 따로 보고합니다.

## 명령어

| 분류 | 명령어 |
| --- | --- |
| String | `SET`, `GET`, `DEL`, `EXISTS`, `DBSIZE`, `KEYS` |
| Memory | `CONFIG SET maxmemory`, `INFO memory` |
| TTL | `EXPIRE`, `TTL` |
| Pub/Sub (보너스) | `PUBLISH`, `SUBSCRIBE` |
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
|   |-- binary_tree.py      # 보너스 3
|   |-- bst.py              # 보너스 4
|   |-- cli.py
|   |-- database.py
|   |-- dynamic_array.py    # 보너스 1
|   |-- hash_map.py
|   |-- linked_list.py
|   |-- min_heap.py
|   `-- pubsub.py           # 보너스 5
|-- tests/
|   |-- test_bonus.py
|   |-- test_database.py
|   |-- test_hash_map.py
|   |-- test_integration.py
|   |-- test_linked_list.py
|   |-- test_memory.py
|   |-- test_min_heap.py
|   |-- test_ttl.py
|   `-- test_project_structure.py
|-- docs/
|   |-- DESIGN.md
|   |-- DEMO.md
|   |-- DISCUSSION.md
|   |-- STACK_QUEUE_DEQUE.md
|   `-- VALIDATION.md
|-- main.py
|-- requirements.txt
`-- README.md
```

## 설계 원칙

- `dict`, `set`, `collections`로 핵심 저장소를 대체하지 않습니다.
- 해시맵은 체이닝으로 충돌을 해결하고 로드 팩터가 0.75를 초과하면 버킷을 두 배로 확장합니다.
- LRU 목록의 삽입, 삭제, 이동은 모두 O(1)로 처리합니다.
- TTL 힙은 `(expire_at, key, version)` 항목을 다루며 오래된 항목은 lazy deletion으로 정리합니다.
- 메모리 사용량은 `len(key.encode("utf-8")) + len(value.encode("utf-8"))`의 합으로 계산합니다.
- 만료, 명시적 삭제, LRU 퇴출은 데이터, LRU, TTL, 메모리 통계를 일관되게 갱신합니다.

## 구현 순서

1. [완료] 이중 연결 리스트와 단위 테스트
2. [완료] 체이닝 해시맵, 리사이징과 단위 테스트
3. [완료] 최소 힙과 단위 테스트
4. [완료] 기본 String 명령 (LRU·TTL 연동은 5~6단계)
5. [완료] 메모리 제한과 LRU 퇴출
6. [완료] TTL과 lazy deletion
7. [완료] CLI 오류 처리와 통합 테스트, 제출 문서 정리
8. [완료] 보너스 과제 1~5

## 메모리와 LRU 동작

성공한 `SET`과 `GET`은 키를 LRU 목록 맨 앞으로 이동합니다.
`EXISTS`, `KEYS`, `DBSIZE`, `INFO`와 실패한 조회는 순서를 바꾸지 않습니다.
자체 해시맵으로 노드를 평균 O(1)에 찾고, 연결 리스트에서 O(1)에 이동합니다.

메모리 제한 기본값과 `0`은 무제한입니다. `CONFIG SET maxmemory`로 제한을
낮춘 경우 과제의 SET 이후 퇴출 규칙에 따라 다음 성공한 SET에서 제한을 적용합니다.
키와 값의 UTF-8 바이트 합이 단독으로 제한을 초과하면 OOM을 반환하며 기존 값과
LRU 순서를 유지합니다. 그 외에는 저장 후 가장 오래 사용하지 않은 키부터 제거합니다.
`evicted_keys`는 LRU 퇴출만 누적하며 명시적 DEL은 포함하지 않습니다.

## TTL 동작

`EXPIRE key seconds`는 초 단위 만료를 지정하고, 0 이하는 즉시 삭제합니다.
`TTL`은 남은 초를 내림하여 반환합니다. 영구 키는 -1, 없는 키는 -2입니다.
시스템 시각 변경의 영향을 피하도록 단조 시계의 정수 나노초를 사용합니다.

최소 힙에는 `(만료시각, 키, 버전)`을 저장합니다. 자체 해시맵의 현재 버전과
다른 힙 항목은 lazy deletion으로 무시합니다. DEL·퇴출·SET 덮어쓰기는 TTL
메타데이터를 즉시 제거하며, 무효 힙 항목은 힙 맨 위에 도달했을 때 정리합니다.
따라서 긴 만료를 반복 설정하면 무효 항목이 일시적으로 남을 수 있습니다.

각 정상 인자 개수의 명령 실행 전에 만료 키를 정리하므로 GET뿐 아니라
KEYS·DBSIZE·INFO에도 만료가 반영됩니다. 입력 대기 중에는 백그라운드 삭제를
수행하지 않습니다. 만료 삭제는 LRU를 갱신하거나 퇴출 횟수를 증가시키지 않습니다.
성공한 SET 덮어쓰기는 TTL을 초기화하며 OOM으로 거절된 SET은 기존 TTL을 유지합니다.

## 보너스 과제

| 번호 | 내용 | 구현 |
| --- | --- | --- |
| 1 | 동적 배열: append/get/set/remove, 용량 2배 확장 | `dynamic_array.py`, 최소 힙의 내부 저장소로 사용 |
| 2 | 스택·큐·덱 조사 | [docs/STACK_QUEUE_DEQUE.md](docs/STACK_QUEUE_DEQUE.md) |
| 3 | 이진 트리와 전위·중위·후위·레벨 순회 | `binary_tree.py`, `from_array`로 힙 배열을 트리로 복원 |
| 4 | BST 삽입·탐색·삭제, 중위 순회 정렬 | `bst.py` |
| 5 | `PUBLISH`, `SUBSCRIBE` | `pubsub.py`, 구독자별 메시지 큐로 연결 리스트 재사용 |

CLI는 단일 세션이므로 `SUBSCRIBE`는 현재 세션을 구독자로 등록하고, 이후 `PUBLISH`가
그 채널로 보낸 메시지를 결과 뒤에 이어서 출력합니다. 실제 Redis처럼 구독 상태에서
다른 명령을 막지는 않습니다.

```text
mini-redis> SUBSCRIBE news
1) "subscribe"
2) "news"
3) (integer) 1
mini-redis> PUBLISH news "hello world"
(integer) 1
1) "message"
2) "news"
3) "hello world"
```
