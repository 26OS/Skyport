from __future__ import annotations

from typing import Optional

from core.models import Counter, Passenger
from schedulers.base import QueueMap, Scheduler, iter_queues, remove_passenger


class NonPreemptiveSJFScheduler(Scheduler):
    name = "Non-preemptive SJF"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Optional[Passenger]:
        del now, counter
        candidates = list(iter_queues(queues))
        if not candidates:
            return None
        best = min(candidates, key=lambda p: (p.service_time, p.arrival_time, p.passenger_id))
        return remove_passenger(queues, best)
