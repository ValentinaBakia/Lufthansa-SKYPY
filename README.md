# SkyPy Crew Rostering

SkyPy Crew Rostering is a small backend service that builds legal crew schedules
for flights and exposes the result through a Flask API.

The project models flights, crew members, roster state, operational rules,
pairing checks, layover costs, and a priority-based scheduler. It also exports
the completed roster to JSON after each scheduling run.

## What It Does

- reads and validates flight and crew data
- builds a roster in priority order using `heapq`
- enforces:
  - range certification
  - home-base start
  - route continuity
  - dynamic rest
  - captain / first officer pairing rules
- calculates layover costs
- exposes the result through three REST endpoints
- exports `output/roster_output.json`

## Tech Stack

- Python 3.11+
- Flask
- Marshmallow
- Pytest
- Ruff

## Project Layout

```text
src/skypy/
├── app.py                  # Flask application factory
├── errors.py               # JSON error handlers
├── models/                 # Domain models
├── services/               # Scheduler, rules, pairing, costs
├── schemas/                # Request / response schemas
├── routes/                 # Flask endpoints
├── state/                  # In-memory latest-run snapshot
└── io/                     # CSV input and JSON export helpers
```

## Setup

Install runtime dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Or for development dependencies:

```bash
python3 -m pip install -r requirements-dev.txt
```

Because the project uses a `src/` layout, the simplest way to work locally is
the editable install:

```bash
python3 -m pip install -e .[dev]
```

## Running the API

From the project root:

```bash
python3 app.py
```

or:

```bash
python3 -m flask --app app.py run
```

The API will expose:

- `POST /schedule`
- `GET /roster/<crew_id>`
- `GET /report`

## API Summary

### `POST /schedule`

Accepts JSON with:

- `flights`
- `crew`

Runs the scheduler, stores the latest result in memory, returns the roster and
unassigned flights, and writes:

```text
output/roster_output.json
```

### `GET /roster/<crew_id>`

Returns:

- assigned flight ids
- total flight hours
- layover cost

### `GET /report`

Returns:

- total scheduled flights
- total unassigned flights
- total layover cost
- per-crew breakdown

## Sample Data and Manual Testing

Sample CSV inputs live in:

```text
data/flights.csv
data/crew.csv
```

To generate an API-ready payload from those CSV files:

```bash
python3 commands/generate_data.py
```

This writes:

```text
output/schedule_payload.json
```

That file can be pasted directly into Postman for `POST /schedule`.

## Output Files

Generated files are written under:

```text
output/
```

Important outputs:
- `output/schedule_payload.json`
- `output/roster_output.json`

## Notes on Design

- Business logic is kept separate from Flask routes.
- The scheduler works on defined objects, not on raw CSV rows or raw JSON.
- CSV loading and API input are two different paths into the same core scheduling engine.
- `GET /roster` and `GET /report` read from the latest in-memory scheduling
  snapshot created by `POST /schedule`.

## Development Notes
Run tests:

```bash
pytest
```
