# Reads data from the CSV files and write the json to be executed for the APIs
import json
from pathlib import Path

from skypy.io.csv_reader import read_crew_csv, read_flights_csv

DATA = Path(__file__).resolve().parent.parent / 'data'
OUTPUT = Path(__file__).resolve().parent.parent / 'output'


def main() -> None:
    flights = read_flights_csv(DATA / 'flights.csv')
    crew = read_crew_csv(DATA / 'crew.csv')

    # Build the /schedule API payload from the same CSV data
    payload = {
        'flights': [
            {
                'flight_id': flight.flight_id,
                'origin': flight.origin,
                'destination': flight.destination,
                'departure': flight.departure.isoformat(),
                'arrival': flight.arrival.isoformat(),
                'distance_miles': flight.distance_miles,
                'priority': int(flight.priority),
            }
            for flight in flights
        ],
        'crew': [
            {
                'crew_id': crew_member.crew_id,
                'home_base': crew_member.home_base,
                'max_range_miles': crew_member.max_range_miles,
                'role': crew_member.role.value,
                'hourly_cost': crew_member.hourly_cost,
            }
            for crew_member in crew
        ],
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    out = OUTPUT / 'schedule_payload.json'
    out.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(f'\n=== API PAYLOAD written to {out} ===')


if __name__ == '__main__':
    main()
