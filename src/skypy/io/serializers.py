"""File-output helpers."""

import json
from pathlib import Path


def write_roster_output(
    total_layover_cost: float, data: dict[str, object], path: str = 'output/roster_output.json'
) -> None:
    out = Path(path)
    out.parent.mkdir(exist_ok=True)
    file_body = dict(data['roster'])
    file_body['unassigned'] = data['unassigned']
    file_body['total_layover_cost'] = total_layover_cost
    out.write_text(json.dumps(file_body, indent=2), encoding='utf-8')
