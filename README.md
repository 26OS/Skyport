# SkyPort Check-in Scheduler

Operating systems term project simulator for non-preemptive multiprocessor check-in counter scheduling.

## Run

Headless run with the HybridMLQ scheduler:

```bash
python3 -m skyport.main --input input.txt --scheduler hybrid
```

Compare all schedulers:

```bash
python3 -m skyport.main --input input.txt --compare
```

Launch the Tkinter GUI:

```bash
python3 -m skyport.main --input input.txt --gui
```

Create a browser-checkable HTML GUI:

```bash
python3 -m skyport.main --input input.txt --scheduler hybrid --web skyport_gui.html
```

The web GUI supports scheduler selection, Play, Pause, Step, Reset, direct time input with `Go`, and timeline slider navigation.

Print the event log:

```bash
python3 -m skyport.main --input input.txt --scheduler hybrid --log
```

## Schedulers

- `fcfs`: first-come, first-served baseline
- `priority`: fixed class priority baseline
- `sjf`: non-preemptive shortest job first baseline
- `hybrid`: HybridMLQ scheduler using class queues, priority protection, spill-over, and HRRN

## Input

Both formats are supported.

CSV:

```csv
passenger_id,arrival_time,class,service_time
P01,0,ECONOMY,7
```

Whitespace assignment format:

```text
1 0 3 7
2 0 1 12
```
