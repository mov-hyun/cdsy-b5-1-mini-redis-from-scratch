# 실행 확인

저장소 루트에서 `python main.py`를 실행한다. Windows에서 python 명령이 없으면
설치된 Python 실행 파일의 절대 경로 또는 `py -3 main.py`를 사용한다.
외부 패키지 설치는 필요 없다.

## 메모리 제한

```text
mini-redis> CONFIG SET maxmemory 30
OK
mini-redis> SET user:1 Alice
OK
mini-redis> SET user:2 Bob
OK
mini-redis> SET user:3 Charlie
OK
mini-redis> GET user:1
(nil)
mini-redis> INFO memory
used_memory:22
maxmemory:30
evicted_keys:1
```

user:1은 11바이트, user:2는 9바이트, user:3은 13바이트다.
총 33바이트에서 가장 오래된 user:1의 11바이트를 빼면 22바이트다.

## 만료와 초기화

```text
mini-redis> EXPIRE user:2 3
(integer) 1
mini-redis> TTL user:2
(integer) 2
```

TTL 값은 입력 속도에 따라 달라진다. 3초 이상 기다린 뒤 GET user:2는
`(nil)`, TTL user:2는 `(integer) -2`다.
SET user:3 Updated 후 TTL user:3은 `(integer) -1`이다.
EXPIRE user:3 0은 `(integer) 1`을 반환하며 즉시 삭제한다.

## 오류 후 계속 실행

```text
mini-redis> CONFIG SET maxmemory abc
(error) ERR value is not an integer or out of range
mini-redis> GET
(error) ERR wrong number of arguments for 'GET' command
mini-redis> HELLO
(error) ERR unknown command 'HELLO'
mini-redis> CONFIG SET maxmemory 1
OK
mini-redis> SET name Alice
(error) OOM command not allowed when used_memory > 'maxmemory'
mini-redis> quit
```

## 자동 검증

`python -m unittest discover -s tests -v`로 자료구조 단위 테스트와 통합 테스트를 실행한다.
`test_integration.py`는 실제 main.py를 별도 프로세스로 실행하여 명령 10종과
오류 복구를 확인한다. 고정 난수 시드로 500회의 혼합 명령 후 구조 일관성도 확인한다.
`test_ttl.py`는 만료 경계와 재설정·재생성·OOM 이후 TTL 보존을 검증한다.
