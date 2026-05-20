# SkyPort

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![pytest](https://img.shields.io/badge/test-pytest-0A9EDC?logo=pytest&logoColor=white)
![Interface](https://img.shields.io/badge/interface-CLI%20%7C%20GUI-4B5563)

공항 체크인 카운터를 CPU, 승객을 프로세스로 모델링한 **비선점형 다중 프로세서 스케줄링 시뮬레이터**입니다. FCFS, Priority, SJF, HybridMLQ의 평균 Turnaround Time(ATT)을 비교할 수 있습니다.

## 핵심 기능

- 5개 카운터에서 4가지 스케줄링 알고리즘 실행 및 ATT 비교
- 승객별 완료 시간과 등급별 ATT 출력
- CLI, Tkinter GUI, 브라우저용 HTML GUI 제공
- CSV 및 공백 구분 입력 지원
- 이벤트 로그로 도착·배정·완료 과정 확인

## 스케줄러

| 키 | 방식 |
| --- | --- |
| `fcfs` | 도착 순서대로 처리 |
| `priority` | FIRST → BUSINESS → ECONOMY 순으로 처리 |
| `sjf` | 서비스 시간이 짧은 승객부터 처리 |
| `hybrid` | 등급별 큐, 전용 카운터, SJF work stealing, Economy aging 조합 |

## 요구 사항

- Python 3.10 이상
- Tkinter (데스크톱 GUI 실행 시)
- pytest (테스트 실행 시에만 필요)

시뮬레이터 실행에는 별도의 외부 Python 패키지가 필요하지 않습니다.

## 프로젝트 구조

```text
Skyport/
├── core/           # 모델, 시뮬레이션 엔진, 스냅샷
├── data_io/        # 입력 파서와 결과 출력
├── gui/            # Tkinter 및 HTML GUI
├── schedulers/     # FCFS, Priority, SJF, HybridMLQ
├── tests/          # 테스트
├── docs/           # 설계 명세와 보고서
├── input.txt       # 기본 입력 데이터
└── main.py         # 실행 진입점
```

## 실행

```bash
cd Skyport

# 기본 실행 (HybridMLQ)
python3 main.py --input input.txt --scheduler hybrid

# 모든 스케줄러 비교
python3 main.py --input input.txt --compare

# Tkinter GUI
python3 main.py --input input.txt --gui

# 브라우저용 HTML 생성
python3 main.py --input input.txt --scheduler hybrid --web skyport_gui.html

# 이벤트 로그 출력
python3 main.py --input input.txt --scheduler hybrid --log
```

전체 명령행 옵션은 다음 명령으로 확인할 수 있습니다.

```bash
python3 main.py --help
```

`--web` 명령은 지정한 경로에 브라우저에서 바로 열 수 있는 HTML 파일을 생성합니다.

## 테스트

pytest를 설치한 뒤 프로젝트 루트에서 실행합니다.

```bash
python3 -m pip install pytest
python3 -m pytest tests/
```

## 입력 형식

열 순서는 `id`, `arrival_time`, `class`, `service_time`입니다. 등급은 `1`(FIRST), `2`(BUSINESS), `3`(ECONOMY)입니다.

```text
# 공백 구분
1 0 3 7
2 0 1 12
```

```csv
passenger_id,arrival_time,class,service_time
P01,0,ECONOMY,7
```

## 문서

- [HybridMLQ 설계 및 평가](docs/HYBRID_MLQ_PAPER.tex)
