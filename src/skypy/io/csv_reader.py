"""Read CSV files into validated domain models."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from skypy.models import Crew, CrewRole, Flight, FlightPriority

FLIGHT_FIELDS = frozenset(
    {
        'flight_id',
        'origin',
        'destination',
        'departure',
        'arrival',
        'distance_miles',
        'priority',
    }
)
CREW_FIELDS = frozenset({'crew_id', 'home_base', 'max_range_miles', 'role', 'hourly_cost'})


def read_flights_csv(path: str | Path) -> list[Flight]:
    """Read a CSV file into validated flights."""
    flights: list[Flight] = []

    for row_number, row in _read_rows(path, FLIGHT_FIELDS):
        try:
            flights.append(
                Flight(
                    flight_id=row['flight_id'],
                    origin=row['origin'],
                    destination=row['destination'],
                    departure=_parse_timestamp(row['departure']),
                    arrival=_parse_timestamp(row['arrival']),
                    distance_miles=int(row['distance_miles']),
                    priority=FlightPriority(int(row['priority'])),
                )
            )
        except (TypeError, ValueError) as error:
            raise ValueError(f'Invalid flight at row {row_number}: {error}') from error

    return flights


def read_crew_csv(path: str | Path) -> list[Crew]:
    """Read a CSV file into validated crew members."""
    crew_members: list[Crew] = []

    for row_number, row in _read_rows(path, CREW_FIELDS):
        try:
            crew_members.append(
                Crew(
                    crew_id=row['crew_id'],
                    home_base=row['home_base'],
                    max_range_miles=int(row['max_range_miles']),
                    role=CrewRole(row['role']),
                    hourly_cost=float(row['hourly_cost']),
                )
            )
        except (TypeError, ValueError) as error:
            raise ValueError(f'Invalid crew at row {row_number}: {error}') from error

    return crew_members


def _read_rows(
    path: str | Path, required_fields: frozenset[str]
) -> Iterable[tuple[int, dict[str, str]]]:
    """Yield CSV rows after confirming all required columns are present."""
    with Path(path).open(newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = set(reader.fieldnames or [])
        missing_fields = required_fields - fieldnames

        if missing_fields:
            missing = ', '.join(sorted(missing_fields))
            raise ValueError(f'Missing required CSV columns: {missing}')

        for row_number, row in enumerate(reader, start=2):
            yield row_number, row


def _parse_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 timestamp, including the common trailing Z form."""
    if not isinstance(value, str):
        raise ValueError('timestamp must be a string')

    normalized_value = f'{value[:-1]}+00:00' if value.endswith('Z') else value

    try:
        return datetime.fromisoformat(normalized_value)
    except ValueError as error:
        raise ValueError(f'{value!r} is not a valid ISO 8601 timestamp') from error
