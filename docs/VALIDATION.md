# 검증 기록

2026-09-11, Windows에서 번들 Python 3.12.14로 실행했다.

```text
python -m unittest discover -s tests -q
Ran 52 tests
OK
```

Python 3.8 문법은 AST 파서로 검사했으며, Python 3.8 런타임 자체에서 실행한 결과는 아니다.
테스트 통과는 검증한 사례에 대한 결과이며 실제 Redis와의 전체 호환성을 의미하지 않는다.

| 과제 요구 | 구현 | 검증 |
| --- | --- | --- |
| 이중 연결 리스트 6개 연산 | linked_list.py | test_linked_list.py |
| 직접 해시·체이닝·0.75 초과 시 확장 | hash_map.py | test_hash_map.py |
| 최소 힙·상향/하향 정렬 | min_heap.py | test_min_heap.py |
| 기본 명령 6개·인자 오류·출력 | database.py, cli.py | test_database.py |
| UTF-8 메모리·OOM·LRU·통계 | database.py | test_memory.py |
| TTL·즉시 만료·덮어쓰기·재생성 | database.py | test_ttl.py |
| 실제 CLI와 오류 복구 | main.py | test_integration.py |
| dict/set/collections 미사용 | mini_redis 전체 | AST 검사 및 코드 검토 |

통합 검증은 500회 혼합 명령 후 메모리 재계산 값, 저장소와 LRU 키 집합,
노드 포인터, TTL 유효성을 확인한다. 고정 시드 20260911로 재현한다.
별도 프로세스로 CLI에 명령 10종을 전달하고 종료 코드·표준 오류·출력을 검사했다.
EOF와 KeyboardInterrupt 종료도 별도 확인했다.

설계상 선택은 다음과 같다.

- CONFIG로 제한을 낮추면 다음 성공한 SET에서 퇴출한다.
- TTL은 남은 초를 내림하며 만료 경계에서는 없는 키로 처리한다.
- 만료는 명령 실행 전에 정리하고 백그라운드 스레드는 사용하지 않는다.
- DEL과 퇴출은 TTL 메타데이터를 즉시 제거하며 무효 힙 기록은 나중에 버린다.
- 선택 보너스는 제출 범위에 포함하지 않는다.

이 문서는 원래 Mini Redis 과제 설명에 대응한다. 성능 벤치마크 수치는 측정하지 않았으며
시간복잡도 설명은 코드의 자료구조와 연산 과정을 근거로 한다.
