"""Rebuild the lesson's shots dataset from Impect Open Data with kloppy.

This is the "pro pipeline" version of what the notebook does by hand:
kloppy (the industry-standard data loader) fetches and standardizes every
shot of the Bundesliga 2023/24 season, and we export a tidy CSV.

The output (data/shots_bundesliga_2023_24.csv) is NOT committed to git -
Impect's terms do not allow redistributing the data, so everyone builds
their own copy. Using the data means accepting their terms:
https://github.com/ImpectAPI/open-data/blob/main/LICENSE.pdf

Usage:
    python scripts/build_dataset.py                # full season, 306 matches
    python scripts/build_dataset.py --matchdays 3  # quick sample
"""

import argparse
import json
import math
import os
import time
import urllib.request

import pandas as pd
from kloppy import impect
from kloppy.domain import (
    BodyPart,
    BodyPartQualifier,
    Orientation,
    SetPieceQualifier,
    SetPieceType,
)

BUNDESLIGA_23_24_ITERATION = 743
MATCHES_PER_MATCHDAY = 9
PITCH_LENGTH, PITCH_WIDTH = 105.0, 68.0  # meters
HALF_GOAL_WIDTH = 3.66


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--matchdays", type=int, default=34)
    args = parser.parse_args()

    base = "https://raw.githubusercontent.com/ImpectAPI/open-data/main/data"
    with urllib.request.urlopen(
        f"{base}/matches/matches_{BUNDESLIGA_23_24_ITERATION}.json"
    ) as r:
        match_list = json.load(r)
    matches = [m for m in match_list if m.get("available")]
    matches.sort(key=lambda m: (m["matchDay"]["index"], m["scheduledDate"]))
    matches = matches[: args.matchdays * MATCHES_PER_MATCHDAY]

    rows = []
    t0 = time.time()
    for i, match in enumerate(matches):
        # orient every event so the shooting team attacks left to right
        events = impect.load_open_data(match_id=match["id"]).transform(
            to_orientation=Orientation.ACTION_EXECUTING_TEAM
        )
        for shot in events.filter("shot"):
            if shot.coordinates is None:
                continue  # a handful of shots have no location recorded
            # kloppy gives normalized coordinates on a 105 x 68 pitch;
            # the goal being attacked is at (105, 34)
            x = shot.coordinates.x * PITCH_LENGTH
            y = shot.coordinates.y * PITCH_WIDTH
            distance = math.hypot(PITCH_LENGTH - x, PITCH_WIDTH / 2 - y)
            angle = math.degrees(
                abs(
                    math.atan2(HALF_GOAL_WIDTH - (y - PITCH_WIDTH / 2), PITCH_LENGTH - x)
                    - math.atan2(-HALF_GOAL_WIDTH - (y - PITCH_WIDTH / 2), PITCH_LENGTH - x)
                )
            )
            body_part = next(
                (q.value for q in shot.qualifiers if isinstance(q, BodyPartQualifier)),
                None,
            )
            set_piece = next(
                (q.value for q in shot.qualifiers if isinstance(q, SetPieceQualifier)),
                None,
            )
            rows.append(
                {
                    "match_id": match["id"],
                    "player": str(shot.player) if shot.player else None,
                    "team": str(shot.team) if shot.team else None,
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "distance": round(distance, 2),
                    "angle": round(angle, 2),
                    "is_header": body_part == BodyPart.HEAD,
                    "is_penalty": set_piece == SetPieceType.PENALTY,
                    "goal": shot.result.name == "GOAL",
                }
            )
        print(
            f"[{i + 1}/{len(matches)}] match {match['id']}: {len(rows)} shots so far",
            flush=True,
        )

    df = pd.DataFrame(rows)
    os.makedirs("data", exist_ok=True)
    out = "data/shots_bundesliga_2023_24.csv"
    df.to_csv(out, index=False)
    print(
        f"wrote {out}: {len(df)} shots, {int(df['goal'].sum())} goals "
        f"in {time.time() - t0:.0f}s"
    )


if __name__ == "__main__":
    main()
