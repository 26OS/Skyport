from __future__ import annotations

from typing import Optional

from core.models import Counter, Passenger
from schedulers.base import QueueMap, Scheduler, fcfs_key, iter_queues, remove_passenger


class FCFSScheduler(Scheduler):
    name = "FCFS"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Optional[Passenger]:
        del now, counter
        candidates = list(iter_queues(queues))
        if not candidates:
            return None
        return remove_passenger(queues, min(candidates, key=fcfs_key))
