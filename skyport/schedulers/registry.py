from __future__ import annotations

from skyport.schedulers.fcfs import FCFSScheduler
from skyport.schedulers.fixed_priority import FixedPriorityScheduler
from skyport.schedulers.multilevel import HybridMLQScheduler
from skyport.schedulers.np_sjf import NonPreemptiveSJFScheduler

SCHEDULERS = {
    "fcfs": FCFSScheduler,
    "priority": FixedPriorityScheduler,
    "sjf": NonPreemptiveSJFScheduler,
    "hybrid": HybridMLQScheduler,
}

