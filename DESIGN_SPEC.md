# SkyPort 체크인 스케줄러 — 디자인 스펙 (Design Specification)

**문서 버전**: 0.1 (초안)
**작성일**: 2026-05-13
**대상 과제**: 운영체제 Term Project — 공항 체크인 카운터 시뮬레이션

---

## 0. 문서 목적

본 문서는 운영체제 Term Project의 **시뮬레이터 본체 + GUI**에 대한 설계 사양을 기술한다. 본 문서는 다음을 정의한다:

- 시스템 범위와 비범위
- 도메인 모델과 인터페이스
- 모듈 아키텍처 및 의존성 방향
- 핵심 알고리즘 (스케줄러 4종)
- 시뮬레이션 엔진 동작 사양 (결정성·tie-break 포함)
- GUI 구성 및 엔진-뷰 결합 규칙
- 테스트·검증 전략
- 산출물(Phase 1/2/3) 매핑

본 문서는 구현에 앞서 합의해야 할 **설계 결정의 단일 진실원(SSOT)**을 목표로 하며, 구현 중 변경된 사항은 본 문서에 역반영한다.

---

## 1. 시스템 개요

### 1.1 문제 정의

5개의 체크인 카운터(C1~C5)에서 50명의 승객을 처리하는 비선점형(Non-preemptive) 멀티프로세서 스케줄링 시뮬레이터를 구현한다. 단일 성능 지표는 **전체 평균 Turnaround Time (ATT)**이다.

### 1.2 범위 (In Scope)

- 비선점형 멀티레벨 스케줄러 (학생 설계, 3개 이상 알고리즘 조합)
- Baseline 스케줄러 3종 (FCFS / Fixed-Priority / Non-preemptive SJF)
- 이산사건 기반 결정적 시뮬레이션 엔진
- 결과 출력 (승객별 / 등급별 / 전체)
- 실시간 시각화 GUI (카운터·큐·간트차트·메트릭)
- 스케줄러 비교 모드

### 1.3 비범위 (Out of Scope)

- 점유(Preemption), Context Switching Overhead
- 카운터별 이종 처리 속도
- 다중 데이터셋 자동 생성 (수동 로드만 지원)
- 네트워크/멀티 인스턴스
- 로그인·세션·영속화

### 1.4 핵심 매핑 (OS ↔ 도메인)

| OS 개념 | 도메인 객체 |
|---|---|
| CPU | Counter (C1~C5) |
| Process | Passenger |
| Burst Time | service_time |
| Priority | class (FIRST=1, BUSINESS=2, ECONOMY=3) |
| Ready Queue | 등급별/통합 대기열 |
| Non-preemptive | 서비스 시작 후 완료 보장 |

---

## 2. 도메인 모델

### 2.1 엔티티

```
Passenger
  - passenger_id : str          (e.g., "P01")
  - arrival_time : int          (0..60)
  - cls          : Class        (FIRST | BUSINESS | ECONOMY)
  - service_time : int          (>=1)
  -- runtime fields --
  - service_start_time : int?   (default None)
  - completion_time    : int?   (default None)
  - turnaround_time    : int?   (= completion - arrival)

Counter
  - counter_id : str            ("C1".."C5")
  - kind       : CounterKind    (FIRST_ONLY | BUSINESS_ONLY | ECONOMY_ONLY | FLEX)
  - current    : Passenger?     (현재 서비스 중)
  - remaining  : int            (남은 service ticks)

Event
  - time   : int
  - kind   : ARRIVAL | DISPATCH | COMPLETION
  - actor  : Passenger | Counter
```

### 2.2 카운터 구성 (고정)

| ID | 종류 | 허용 등급 |
|---|---|---|
| C1 | FIRST_ONLY | FIRST |
| C2 | BUSINESS_ONLY | BUSINESS |
| C3 | ECONOMY_ONLY | ECONOMY |
| C4 | FLEX | ALL |
| C5 | FLEX | ALL |

**설계 결정 (D-1) — 전용 카운터 spill-over**: 전용 카운터가 idle이고 본 등급 대기열이 비어있을 때, **하위 등급(FIRST→BUSINESS→ECONOMY 우선 순서) 승객을 수용한다.** 근거: Economy 비율이 64%로 높아 strict 정책은 유휴를 크게 만들고 ATT를 악화시킨다.

**설계 결정 (D-2) — Flex 카운터 디스패치**: Flex 카운터는 비어 있을 때 **HRRN(Highest Response Ratio Next)** 기준으로 등급 무관하게 선택한다. 이는 starvation을 자연스럽게 완화한다.

---

## 3. 모듈 아키텍처

### 3.1 패키지 구조 (Python 가정)

```
skyport/
├── core/
│   ├── models.py         # Passenger, Counter, Event, enums
│   ├── snapshot.py       # SimSnapshot (immutable)
│   ├── engine.py         # SimulationEngine
│   └── logger.py         # EventLogger
├── schedulers/
│   ├── base.py           # Scheduler (Strategy interface)
│   ├── fcfs.py           # BaselineA
│   ├── fixed_priority.py # BaselineB
│   ├── np_sjf.py         # BaselineC
│   └── multilevel.py     # 학생 설계 (Priority + HRRN + SJF)
├── io/
│   ├── parser.py         # CSV/TXT 입력 파싱
│   └── reporter.py       # CSV/표 출력, 통계
├── gui/
│   ├── app.py            # 메인 윈도우, 컨트롤러
│   ├── views/
│   │   ├── counters.py
│   │   ├── queues.py
│   │   ├── gantt.py
│   │   └── metrics.py
│   └── controllers.py    # 사용자 명령 → 엔진 호출
└── main.py               # --headless / --gui 진입점
```

### 3.2 의존성 방향 (Dependency Rule)

```
gui  ──▶  core  ◀──  schedulers
 │         ▲             │
 └────▶ io ┘             │
           ▲             │
           └─────────────┘
```

- `core`는 어떤 모듈에도 의존하지 않는다.
- `schedulers`는 `core.models`만 의존한다 (엔진/GUI 모름).
- `gui`는 `core`와 `schedulers`만 import 한다.
- **역방향 import 금지** (특히 core → gui).

---

## 4. 핵심 인터페이스

### 4.1 Scheduler (Strategy Pattern)

```python
class Scheduler(ABC):
    name: str

    @abstractmethod
    def select(
        self,
        now: int,
        counter: Counter,
        queues: QueueView,
    ) -> Optional[Passenger]:
        """
        주어진 시각 `now`에 비어있는 `counter`가 다음에 처리할 승객을 반환.
        반환값이 None이면 해당 카운터는 이번 tick에 유휴 상태 유지.
        부수효과: 선택된 승객을 큐에서 제거.
        """
```

**불변식**:
- 반환 승객의 `arrival_time <= now`
- 반환 승객의 등급이 `counter.kind`의 허용 범위에 속함
- 동일 입력에 대해 동일 출력 (결정성)

### 4.2 SimulationEngine

```python
class SimulationEngine:
    def __init__(self, passengers: list[Passenger],
                 counters: list[Counter],
                 scheduler: Scheduler): ...

    def tick(self) -> SimSnapshot:
        """가상 시간을 1 단위 진행하고 새 스냅샷 반환."""

    def run(self) -> SimSnapshot:
        """모든 승객이 완료될 때까지 tick 반복."""

    def reset(self) -> None: ...

    @property
    def is_done(self) -> bool: ...
```

### 4.3 SimSnapshot (불변 DTO)

```python
@dataclass(frozen=True)
class SimSnapshot:
    time: int
    counters: tuple[CounterState, ...]
    queues: Mapping[Class, tuple[PassengerView, ...]]
    completed: tuple[PassengerView, ...]
    metrics: Metrics             # 현재까지의 ATT, 등급별 평균 TAT
    events_this_tick: tuple[Event, ...]
```

GUI는 이 스냅샷만 본다. 엔진 내부 자료구조에 접근하지 않는다.

---

## 5. 시뮬레이션 엔진 동작 사양

### 5.1 메인 루프 (per tick)

각 tick t (0부터 시작) 에서 다음 순서로 처리:

1. **Arrival 처리**: `arrival_time == t`인 승객을 등급별 대기열에 삽입. 동시각 다수 도착 시 `passenger_id` 사전순.
2. **Completion 처리**: `remaining == 0`인 모든 카운터에서 승객을 완료 상태로 전이. `completion_time = t` 기록.
3. **Dispatch**: 빈 카운터를 **C1 → C2 → C3 → C4 → C5 순**으로 순회하며 `Scheduler.select(...)` 호출. 선택된 승객의 `service_start_time = t`, `remaining = service_time`.
4. **Tick 진행**: 각 busy 카운터의 `remaining -= 1`.
5. **Snapshot 발행**.

**중요**: 한 tick 내에서 카운터가 비고(완료) 같은 tick에 새 승객을 받는 것이 가능하다. 이는 유휴 시간 최소화를 위해 필요하며, 위 순서(2 → 3)가 이를 보장한다.

### 5.2 종료 조건

- 모든 승객의 `completion_time`이 설정됨.
- 또는 `time > SAFETY_LIMIT` (예: 1000) — 무한 루프 방어.

### 5.3 결정성 보장 (Tie-breaking 규칙)

| 상황 | 규칙 |
|---|---|
| 동시각 다수 도착 | passenger_id 사전순 |
| 동시각 다수 카운터 idle | counter_id 사전순 (C1→C5) |
| 큐 내 동일 우선순위 다수 | arrival_time 오름, 동일 시 id 사전순 |
| HRRN 동률 | service_time 짧은 것, 동일 시 id 사전순 |

이 규칙은 `Scheduler`와 `Engine` 양쪽에서 일관 적용된다.

### 5.4 비선점 불변식 (Assertion)

- `service_start_time != None` ⇒ `completion_time == service_start_time + service_time`
- 한 카운터에 동시 2명 배정 불가
- 전용 카운터의 class 제약 위반 시 즉시 fail-fast

---

## 6. 스케줄러 명세

### 6.1 Baseline A: FCFS

- 통합 단일 큐, arrival 순서.
- 카운터가 비면 큐 선두 승객을 본다 — 카운터가 수용 가능한 가장 앞의 승객을 선택.

### 6.2 Baseline B: Fixed-Priority

- 등급별 분리 큐 3개.
- 카운터별 허용 등급 중 가장 높은 우선순위(FIRST → BUSINESS → ECONOMY) 큐의 선두 선택.
- 큐 내부는 FCFS.

### 6.3 Baseline C: Non-preemptive SJF

- 통합 큐. `service_time` 짧은 순.
- 카운터의 class 제약은 준수.

### 6.4 학생 설계: HybridMLQ (제안)

**구성 알고리즘 (≥3)**: Multi-Level Queue + Priority + HRRN + (전용 카운터 spill-over 정책)

**큐 구성**: 등급별 분리 큐 3개 (Q_FIRST, Q_BUSINESS, Q_ECONOMY).

**디스패치 규칙**:

| 카운터 | 1순위 | 2순위 (idle 시) |
|---|---|---|
| C1 (First 전용) | Q_FIRST FCFS | Q_BUSINESS → Q_ECONOMY 의 HRRN |
| C2 (Business 전용) | Q_BUSINESS FCFS | Q_ECONOMY 의 HRRN |
| C3 (Economy 전용) | Q_ECONOMY HRRN | (없음 — 등급 위반 방지) |
| C4, C5 (Flex) | 3개 큐 통합 HRRN | — |

**근거**:
- 전용 카운터는 본 등급을 우선 보호 (등급 형평성).
- spill-over로 유휴 최소화 (utilization ↑).
- Flex 카운터의 HRRN은 starvation을 막으면서 짧은 burst를 우선해 ATT 개선.
- Economy 전용 C3는 상위 등급 흡수 불가 — 안전(class 제약).

상세 의사코드는 §10 참조.

---

## 7. 입출력 사양

### 7.1 입력 형식 (CSV)

```
passenger_id,arrival_time,class,service_time
P01,0,ECONOMY,7
P02,0,FIRST,12
...
```

- 헤더 행 필수.
- class는 대소문자 무시.
- 빈 줄·주석(`#`로 시작) 허용.

### 7.2 출력 형식

**stdout / CSV 동시 지원**:

```
passenger_id, arrival_time, service_start_time, completion_time, turnaround_time, counter_id
```

**요약**:
```
Class      Count   Avg TAT
FIRST      8       xx.xx
BUSINESS   10      xx.xx
ECONOMY    32      xx.xx
TOTAL      50      ATT = xx.xx
```

### 7.3 로그

이벤트별 1줄 (시간 오름차순):
```
t=05 ARRIVAL  P07 (FIRST, st=15)
t=05 DISPATCH P07 → C1
t=20 COMPLETE P07 @ C1 (TAT=15)
```

---

## 8. GUI 사양

### 8.1 레이아웃

```
┌──────────────────────────────────────────────────────┐
│  [Scheduler ▾] [Load CSV]  ▶ ⏸ ⏭ ⏹   Speed [——●——]  │
├──────────────────────────────────────────────────────┤
│  Counters (5)                  │  Metrics             │
│  ┌──┐┌──┐┌──┐┌──┐┌──┐         │  Time: 042           │
│  │C1││C2││C3││C4││C5│         │  ATT (so far): 14.2  │
│  └──┘└──┘└──┘└──┘└──┘         │  FIRST avg : 18.0    │
├────────────────────────────────┤  BUSINESS  : 12.4    │
│  Queues                        │  ECONOMY   : 14.9    │
│  FIRST    : [P19 P26 ...]      │  Done: 27/50         │
│  BUSINESS : [P21 P24 ...]      ├──────────────────────┤
│  ECONOMY  : [P22 P23 ...]      │  Event log           │
├────────────────────────────────┤  t=42 DISPATCH ...   │
│  Gantt (counter × time)        │  t=41 COMPLETE ...   │
│  (실시간 막대 증가)            │  ...                 │
└──────────────────────────────────────────────────────┘
```

### 8.2 컨트롤러 명령

| 명령 | 효과 |
|---|---|
| Play | 타이머 시작 (interval = 1000/speed ms) |
| Pause | 타이머 정지 |
| Step | tick 1회 |
| Reset | 엔진 재생성, 시각 0 |
| Speed | 타이머 간격 변경 (즉시 반영) |
| Scheduler ▾ | 변경 시 자동 Reset (실행 중이면 확인) |
| Load CSV | 입력 교체 → Reset |

### 8.3 엔진-뷰 결합 규칙

- 뷰는 `SimSnapshot`만 받는다.
- 모든 위젯 갱신은 GUI 메인 스레드에서 `after()` 콜백으로 수행.
- 엔진은 GUI를 모른다 — `import gui` 금지.
- speed/pause는 GUI 측 타이머만 제어하며, 엔진 내부 결과에 영향 없음.

### 8.4 비교 모드 (선택 기능)

- 4개 스케줄러(FCFS, Fixed-Pri, SJF, Hybrid)를 동일 입력으로 headless 실행.
- 결과 표 + 막대그래프(matplotlib) — Phase 3 보고서에 그대로 첨부.

---

## 9. 기술 스택

| 영역 | 선택 | 근거 |
|---|---|---|
| 언어 | Python 3.11+ | 개발 속도, 시각화 생태계, 과제 허용 |
| GUI | Tkinter + matplotlib | 표준 라이브러리, 추가 의존성 최소 |
| 테스트 | pytest | 표준 |
| 포맷 | ruff / black | 일관성 |

---

## 10. 알고리즘 의사코드 (Hybrid)

```
function select(now, counter, queues):
    if counter.kind == FIRST_ONLY:
        if queues.FIRST not empty:
            return queues.FIRST.pop_front()       # FCFS
        return hrrn_pick(queues.BUSINESS, queues.ECONOMY, now)
    if counter.kind == BUSINESS_ONLY:
        if queues.BUSINESS not empty:
            return queues.BUSINESS.pop_front()
        return hrrn_pick(queues.ECONOMY, now)
    if counter.kind == ECONOMY_ONLY:
        return hrrn_pick(queues.ECONOMY, now)
    if counter.kind == FLEX:
        return hrrn_pick(queues.FIRST, queues.BUSINESS, queues.ECONOMY, now)

function hrrn_pick(*qs, now):
    best, best_rr = None, -inf
    for p in flatten(qs):
        waiting = now - p.arrival_time
        rr = (waiting + p.service_time) / p.service_time
        if rr > best_rr or (rr == best_rr and tiebreak(p, best)):
            best, best_rr = p, rr
    if best: remove best from its queue
    return best
```

---

## 11. 검증 및 테스트 전략

### 11.1 단위 테스트

- 각 스케줄러: 손계산 가능한 3~5명 입력에 대한 정확한 ATT 일치.
- HRRN 계산: 경계값 (waiting=0).
- Tie-breaking: 동시각 도착·동시각 idle 카운터.

### 11.2 불변식 어서션 (런타임)

- 카운터당 동시 1명 이하.
- class 제약 위반 0건.
- `completion - service_start == service_time`.

### 11.3 회귀 테스트

- 기본 데이터셋 50명에 대한 4개 스케줄러 ATT를 골든 파일로 고정.
- GUI 실행 후 최종 ATT == headless 실행 ATT (정확히 일치).

### 11.4 수동 검증

- 간트차트에서 유휴 구간이 spill-over 정책과 일치하는지 시각 확인.
- 등급별 평균 TAT가 직관(FIRST < BUSINESS < ECONOMY 예상)과 어긋날 경우 근거 분석.

---

## 12. 산출물 매핑 (과제 Phase ↔ 본 문서)

| 과제 항목 | 본 문서 위치 |
|---|---|
| Phase 1 설계서 | §2(D-1, D-2), §6, §10 |
| Phase 2 구현 | §3, §4, §5, §7 |
| Phase 3 비교 분석 | §6.1~6.3, §8.4, §11.3 |
| 출력 요구 | §7.2 |
| Strategy Pattern 요구 | §4.1, §3.2 |

---

## 13. 위험 및 완화 (Risk Register)

| ID | 위험 | 영향 | 완화 |
|---|---|---|---|
| R1 | GUI ↔ 엔진 결합 | Phase 3 비교 신뢰성 붕괴 | §3.2 의존성 규칙, §4.3 스냅샷 |
| R2 | 비결정적 tie-break | 보고서 수치 흔들림 | §5.3 명시 규칙 |
| R3 | spill-over 정책이 등급 형평성 훼손 | 보고서 정당화 곤란 | §11 수동 검증, trade-off 분석 |
| R4 | GUI가 일정 잠식 | Phase 2/3 지연 | §14 우선순위 명시 |
| R5 | 단일 데이터셋 과적합 | 일반화 부족 | 추가 데이터셋 1~2개 자체 생성 |

---

## 14. 구현 우선순위 / 마일스톤

| 순서 | 마일스톤 | 완료 정의 |
|---|---|---|
| M1 | core + Baseline A | headless로 50명 FCFS ATT 출력 |
| M2 | Baseline B, C | 3개 baseline ATT 골든 파일 확정 |
| M3 | Hybrid 스케줄러 | baseline 대비 ATT 개선 확인 |
| M4 | 최소 GUI | 카운터 5개 + play/pause + ATT |
| M5 | 큐·간트·메트릭 뷰 | 시각 검증 가능 |
| M6 | 비교 모드 | Phase 3 그래프 자동 생성 |
| M7 | 보고서 작성 | trade-off·한계 포함 |

---

## 15. 변경 이력

| 버전 | 일자 | 변경 내용 |
|---|---|---|
| 0.1 | 2026-05-13 | 초안 작성 |
