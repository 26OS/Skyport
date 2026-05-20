from __future__ import annotations

from collections.abc import Iterable
from typing import Optional

from core.models import CLASS_ORDER, Counter, CounterKind, Passenger, PassengerClass
from schedulers.base import QueueMap, Scheduler, hrrn_sort_key, iter_queues, remove_passenger

ECONOMY_AGING_THRESHOLD = 10


class HybridMLQScheduler(Scheduler):
    name = "HybridMLQ"

    def select(self, now: int, counter: Counter, queues: QueueMap) -> Optional[Passenger]:
        own_class = _own_class(counter)
        if own_class is not None and queues[own_class]:
            return _pick_from_class(now, queues, own_class)
        return _pick_sjf(queues, (cls for cls in CLASS_ORDER if cls is not own_class))


def _own_class(counter: Counter) -> Optional[PassengerClass]:
    if counter.kind is CounterKind.FIRST_ONLY:
        return PassengerClass.FIRST
    if counter.kind is CounterKind.BUSINESS_ONLY:
        return PassengerClass.BUSINESS
    if counter.kind is CounterKind.ECONOMY_ONLY:
        return PassengerClass.ECONOMY
    return None


def _pick_from_class(now: int, queues: QueueMap, cls: PassengerClass) -> Passenger:
    if cls is PassengerClass.ECONOMY:
        best = min(
            (p for p in queues[cls] if now - p.arrival_time >= ECONOMY_AGING_THRESHOLD),
            key=lambda p: hrrn_sort_key(now, p),
            default=None,
        )
        if best is not None:
            return remove_passenger(queues, best)
    return _pick_sjf(queues, (cls,))


def _pick_sjf(queues: QueueMap, classes: Iterable[PassengerClass]) -> Optional[Passenger]:
    best = min(iter_queues(queues, classes), key=_sjf_priority_key, default=None)
    if best is None:
        return None
    return remove_passenger(queues, best)


def _sjf_priority_key(passenger: Passenger) -> tuple[int, int, int, str]:
    return (
        passenger.service_time,
        passenger.cls.value,
        passenger.arrival_time,
        passenger.passenger_id,
    )
