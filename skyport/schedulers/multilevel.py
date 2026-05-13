from __future__ import annotations

from typing import Optional

from skyport.core.models import Counter, CounterKind, Passenger, PassengerClass
from skyport.schedulers.base import QueueMap, Scheduler, hrrn_pick


class HybridMLQScheduler(Scheduler):
    name = "HybridMLQ"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Optional[Passenger]:
        if counter.kind is CounterKind.FIRST_ONLY:
            if queues[PassengerClass.FIRST]:
                return queues[PassengerClass.FIRST].popleft()
            return hrrn_pick(now, queues, (PassengerClass.BUSINESS, PassengerClass.ECONOMY))
        if counter.kind is CounterKind.BUSINESS_ONLY:
            if queues[PassengerClass.BUSINESS]:
                return queues[PassengerClass.BUSINESS].popleft()
            return hrrn_pick(now, queues, (PassengerClass.ECONOMY,))
        if counter.kind is CounterKind.ECONOMY_ONLY:
            return hrrn_pick(now, queues, (PassengerClass.ECONOMY,))
        return hrrn_pick(now, queues, (PassengerClass.FIRST, PassengerClass.BUSINESS, PassengerClass.ECONOMY))

