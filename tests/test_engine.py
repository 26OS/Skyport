from skyport.core.engine import SimulationEngine
from skyport.core.models import Passenger, PassengerClass, default_counters
from skyport.io.parser import load_passengers
from skyport.schedulers import FCFSScheduler, HybridMLQScheduler


def test_assignment_input_runs_to_completion():
    passengers = load_passengers("input.txt")
    engine = SimulationEngine(passengers, default_counters(), HybridMLQScheduler())

    snapshot = engine.run()

    assert snapshot.metrics.completed_count == 50
    assert snapshot.metrics.overall_att == 17.92


def test_same_tick_completion_then_dispatch():
    passengers = [
        Passenger("P01", 0, PassengerClass.FIRST, 1),
        Passenger("P02", 1, PassengerClass.FIRST, 1),
    ]
    engine = SimulationEngine(passengers, default_counters(), FCFSScheduler())

    engine.tick()
    snapshot = engine.tick()

    messages = [event.message for event in snapshot.events_this_tick]
    assert any("COMPLETE P01" in message for message in messages)
    assert any("DISPATCH P02" in message for message in messages)


def test_non_preemptive_completion_invariant():
    passengers = load_passengers("input.txt")
    engine = SimulationEngine(passengers, default_counters(), HybridMLQScheduler())

    engine.run()

    for passenger in engine.completed:
        assert passenger.completion_time - passenger.service_start_time == passenger.service_time

