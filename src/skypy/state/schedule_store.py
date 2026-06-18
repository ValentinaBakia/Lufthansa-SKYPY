"""Temporary storage for the latest successful scheduling run."""

from dataclasses import dataclass

from skypy.models.crew import Crew
from skypy.models.flight import Flight
from skypy.models.roster import Roster
from skypy.services.scheduler import UnassignedFlight


@dataclass(frozen=True, slots=True)
class ScheduleSnapshot:
    """
    Latest scheduling result kept in memory.
    `frozen=True` means that it is immutable
    `slots=True` means only the declared attrs are allowed, its a bit more lighter
    """

    roster: Roster
    flights: tuple[Flight, ...]
    crew_members: tuple[Crew, ...]
    unassigned_flights: tuple[UnassignedFlight, ...]
    layover_costs: dict[str, float]
    total_layover_cost: float


class ScheduleStore:
    def __init__(self) -> None:
        self._latest: ScheduleSnapshot | None = None

    def save(self, snapshot: ScheduleSnapshot) -> None:
        """
        Replace the current snapshot with the latest run
        """
        self._latest = snapshot

    def get_latest(self) -> ScheduleSnapshot | None:
        return self._latest
