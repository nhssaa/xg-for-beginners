import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # Your First xG Model

        **A hands-on NHSSAA lesson: teach a computer to grade soccer shots**

        *Inspired by Chris Dove's NHSSAA Summer Symposium webinar (June 2026).
        All code in this notebook is original, written for the NHSSAA community.*

        **xG (expected goals)** is the number you hear on TV: "that shot was 0.35 xG."
        It means: *shots like this one go in about 35% of the time.*

        Today you will build that number yourself, from **8,000+ real Bundesliga shots**,
        one clue at a time. No install needed: press **Run** and everything happens
        right here in your browser.
        """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Step 0 - Get the data

        We use **Impect Open Data**: every event of the 2023/24 Bundesliga season,
        free for learning and research. The notebook downloads match files straight
        from Impect's public repository - by using them you agree to the
        [Impect open-data terms](https://github.com/ImpectAPI/open-data/blob/main/LICENSE.pdf).

        A Bundesliga season has 34 matchdays (9 games each). Loading more matchdays
        gives the model more shots to learn from, but takes longer:

        - **In the browser:** keep it small (1-3 matchdays). Each matchday is ~50 MB.
        - **On your own computer:** crank it to 34 for all ~8,069 shots.
        """
    )
    return


@app.cell
def _(mo):
    matchday_picker = mo.ui.slider(
        start=1, stop=34, value=2, label="Matchdays to load", show_value=True
    )
    load_form = matchday_picker.form(
        submit_button_label="Load the shots", bordered=False
    )
    mo.vstack([mo.md("### Pick how much data to use"), load_form])
    return (load_form,)


@app.cell
def _():
    import json
    import math
    import sys
    import urllib.request

    if "pyodide" in sys.modules:  # running inside the browser
        import pyodide_http

        pyodide_http.patch_all()

    DATA_BASE_URL = (
        "https://raw.githubusercontent.com/ImpectAPI/open-data/main/data"
    )

    def load_json(url):
        with urllib.request.urlopen(url) as _response:
            return json.load(_response)

    return DATA_BASE_URL, load_json, math


@app.cell
def _(DATA_BASE_URL, load_form, load_json, mo):
    n_matchdays = load_form.value if load_form.value is not None else 2

    # The list of every match in the season lives in one small file.
    match_list = load_json(f"{DATA_BASE_URL}/matches/matches_743.json")
    available_matches = [m for m in match_list if m.get("available")]
    available_matches.sort(
        key=lambda m: (m["matchDay"]["index"], m["scheduledDate"])
    )

    matches_to_load = available_matches[: n_matchdays * 9]

    raw_shots = []
    with mo.status.progress_bar(
        total=len(matches_to_load), title="Downloading matches"
    ) as bar:
        for match in matches_to_load:
            events = load_json(
                f"{DATA_BASE_URL}/events/events_{match['id']}.json"
            )
            for event in events:
                if event.get("actionType") == "SHOT" and event.get("shot"):
                    raw_shots.append(event)
            bar.update()

    mo.md(
        f"Loaded **{len(raw_shots):,} shots** from "
        f"**{len(matches_to_load)} matches**."
    )
    return (raw_shots,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Step 1 - Meet a shot

        Every shot in the data answers a few simple questions:

        | question | field in the data |
        |---|---|
        | where was the shooter? | `start.adjCoordinates` (x, y in meters) |
        | foot or head? | `bodyPart` |
        | was it a penalty? | `action == "PENALTY_KICK"` |
        | did it go in? | `result == "SUCCESS"` |

        Coordinates are in meters, with the center circle at (0, 0) and the goal
        the shooter attacks at **(52.5, 0)**. From x and y we can compute the two
        most famous clues in shot analysis:

        - **distance** - how far from the goal?
        - **angle** - how much of the goal can the shooter see?
        """
    )
    return


@app.cell
def _(math, raw_shots):
    import pandas as pd

    GOAL_X = 52.5  # goal line, in meters
    GOAL_Y = 0.0  # middle of the goal
    HALF_GOAL_WIDTH = 3.66  # goal posts are 7.32 m apart

    rows = []
    for shot in raw_shots:
        point = shot["start"]["adjCoordinates"]
        x, y = point["x"], point["y"]

        # clue 1: straight-line distance to the middle of the goal
        distance = math.hypot(GOAL_X - x, GOAL_Y - y)

        # clue 2: the angle between the two goal posts, seen from the shot
        to_near_post = math.atan2(HALF_GOAL_WIDTH - y, GOAL_X - x)
        to_far_post = math.atan2(-HALF_GOAL_WIDTH - y, GOAL_X - x)
        angle = math.degrees(abs(to_near_post - to_far_post))

        rows.append(
            {
                "x": x,
                "y": y,
                "distance": round(distance, 2),
                "angle": round(angle, 2),
                "is_header": shot.get("bodyPart") == "HEAD",
                "is_penalty": shot.get("action") == "PENALTY_KICK",
                "goal": shot.get("result") == "SUCCESS",
            }
        )

    shots = pd.DataFrame(rows)
    shots
    return HALF_GOAL_WIDTH, GOAL_X, GOAL_Y, pd, shots


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Step 2 - See every shot at once

        A map of the season so far. Green dots are goals. Notice where they cluster -
        that picture is the whole idea behind xG.
        """
    )
    return


@app.cell
def _(GOAL_X, shots):
    from mplsoccer import Pitch

    pitch = Pitch(
        pitch_type="uefa", pitch_color="grass", line_color="white", stripe=True
    )
    fig, ax = pitch.draw(figsize=(12, 8))

    # mplsoccer's uefa pitch runs 0..105 x 0..68; our data is centered on (0, 0)
    plot_x = shots["x"] + GOAL_X
    plot_y = shots["y"] + 34

    pitch.scatter(
        plot_x[~shots["goal"]],
        plot_y[~shots["goal"]],
        s=18,
        color="#1f77b4",
        alpha=0.35,
        label="no goal",
        ax=ax,
    )
    pitch.scatter(
        plot_x[shots["goal"]],
        plot_y[shots["goal"]],
        s=30,
        color="#2ca02c",
        edgecolors="black",
        label="goal",
        ax=ax,
    )
    ax.legend(loc="lower left", fontsize=12)
    fig
    return (pitch,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Clue 1 - Distance

        Guess first: does distance matter? Let's let the data answer.

        We bucket shots by how far out they were and count how often each
        bucket scored.
        """
    )
    return


@app.cell
def _(pd, shots):
    distance_buckets = pd.cut(
        shots["distance"],
        bins=[0, 6, 11, 16, 23, 32, 80],
        labels=["0-6 m", "6-11 m", "11-16 m", "16-23 m", "23-32 m", "32+ m"],
    )
    clue1 = (
        shots.groupby(distance_buckets, observed=True)["goal"]
        .agg(shots="size", goals="sum", goal_rate="mean")
        .round(3)
    )
    clue1
    return (clue1,)


@app.cell
def _(clue1):
    import matplotlib.pyplot as plt

    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.bar(clue1.index.astype(str), clue1["goal_rate"], color="#1f77b4")
    ax1.set_ylabel("fraction of shots that scored")
    ax1.set_xlabel("distance from goal")
    ax1.set_title("Closer is better (no surprise) - but by how much?")
    fig1
    return ()


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Clue 2 - Angle

        Two shots from the **same distance** are not equal: one in front of goal,
        one near the sideline. The difference is how much of the goal mouth the
        shooter can see - the **angle**.

        Look at the map below: color = how often shots from that spot scored.
        Distance alone can't draw this picture.
        """
    )
    return


@app.cell
def _(plt, shots):
    import numpy as np

    fig2, ax2 = plt.subplots(figsize=(8, 5))
    grid = ax2.hist2d(
        shots["distance"],
        shots["angle"],
        bins=[12, 12],
        weights=shots["goal"],
        cmap="Greens",
    )
    counts, _, _ = np.histogram2d(
        shots["distance"], shots["angle"], bins=[12, 12]
    )
    # redraw as a goal-rate heatmap so color means "chance", not "volume"
    ax2.clear()
    rate = np.divide(
        grid[0], counts, out=np.zeros_like(grid[0]), where=counts > 25
    )
    img = ax2.imshow(
        rate.T,
        origin="lower",
        aspect="auto",
        extent=[
            shots["distance"].min(),
            shots["distance"].max(),
            shots["angle"].min(),
            shots["angle"].max(),
        ],
        cmap="Greens",
    )
    fig2.colorbar(img, ax=ax2, label="goal rate")
    ax2.set_xlabel("distance (m)")
    ax2.set_ylabel("angle (degrees)")
    ax2.set_title("Distance x angle: the two strongest clues together")
    fig2
    return (np,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Clue 3 - Head or foot?

        Headers are harder: the ball comes in the air, you have less control.
        Same distance, very different story.
        """
    )
    return


@app.cell
def _(shots):
    clue3 = (
        shots[shots["distance"] < 16]
        .groupby("is_header")["goal"]
        .agg(shots="size", goals="sum", goal_rate="mean")
        .round(3)
    )
    clue3
    return (clue3,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Clue 4 - Penalties break the pattern

        A penalty is always from the same spot, with no defender in the way.
        No model of "normal" shots can price it - so analysts **hard-code** it.

        Historically about **76%** of penalties are scored, so xG models just say:

        > penalty = 0.76 xG, always.

        Check the data yourself below - how close is this season to 0.76?
        """
    )
    return


@app.cell
def _(shots):
    penalties = shots[shots["is_penalty"]]
    penalty_rate = penalties["goal"].mean()
    penalty_summary = {
        "penalties": int(len(penalties)),
        "scored": int(penalties["goal"].sum()),
        "conversion rate": round(float(penalty_rate), 3),
        "the hard-coded xG value": 0.76,
    }
    penalty_summary
    return (penalty_summary,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Step 3 - Does each clue actually help?

        Time to be scientists. We train tiny models that each see **one more clue**
        than the last, and measure the error with **log loss** (lower = better at
        putting high numbers on real goals and low numbers on misses).

        1. **No clues** - predict the same average for every shot
        2. **+ distance**
        3. **+ angle**
        4. **+ header?**
        5. penalties handled by the hard-coded 0.76
        """
    )
    return


@app.cell
def _(np, pd, shots):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import log_loss
    from sklearn.model_selection import train_test_split

    train_all, test = train_test_split(shots, test_size=0.25, random_state=42)
    train = train_all[~train_all["is_penalty"]].copy()
    test_open = test[~test["is_penalty"]]

    clue_sets = {
        "no clues (just the average)": [],
        "clue 1: distance": ["distance"],
        "clues 1-2: + angle": ["distance", "angle"],
        "clues 1-3: + header": ["distance", "angle", "is_header"],
    }

    clue_scores = []
    for label, features in clue_sets.items():
        if features:
            mini_model = LogisticRegression(max_iter=1000)
            mini_model.fit(train[features], train["goal"])
            predictions = mini_model.predict_proba(test_open[features])[:, 1]
        else:
            predictions = [train["goal"].mean()] * len(test_open)
        clue_scores.append(
            {
                "model": label,
                "log loss": round(log_loss(test_open["goal"], predictions), 4),
            }
        )

    pd.DataFrame(clue_scores)
    return log_loss, test, test_open, train


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Step 4 - The real model: gradient-boosted trees

        Pros don't stop at straight-line rules. **LightGBM** (a
        gradient-boosted trees model - the kind used at real clubs) learns
        curves and combinations on its own: how distance matters *differently*
        at big angles, how headers change everything, and so on.

        Below we train it on all non-penalty shots, then glue the two pieces
        together:

        - normal shots: the model's prediction
        - penalties: the hard-coded 0.76

        A fair warning from real life: with only three clues, the simple models
        above are already very good, and the fancy model only matches them.
        Boosted trees earn their keep when you feed them *more* clues -
        that is exactly what the challenges at the end ask you to do.
        """
    )
    return


@app.cell
def _(np, shots, test, train):
    import sys as _sys

    FEATURES = ["distance", "angle", "is_header"]

    if "pyodide" in _sys.modules:
        # In the browser we use scikit-learn's gradient boosting - the same
        # idea as LightGBM. On your own computer: pip install lightgbm and
        # the notebook uses the real thing automatically.
        from sklearn.ensemble import HistGradientBoostingClassifier

        model = HistGradientBoostingClassifier(
            max_iter=50, max_leaf_nodes=7, learning_rate=0.05, random_state=42
        )
        model_name = "scikit-learn gradient boosting (browser edition)"
    else:
        import lightgbm as lgb

        model = lgb.LGBMClassifier(
            n_estimators=50,
            learning_rate=0.05,
            num_leaves=7,
            min_child_samples=100,
            random_state=42,
            verbose=-1,
        )
        model_name = "LightGBM"

    model.fit(train[FEATURES], train["goal"])

    # full xG: model for open play, 0.76 for penalties
    PENALTY_XG = 0.76

    test_xg = np.where(
        test["is_penalty"], PENALTY_XG, model.predict_proba(test[FEATURES])[:, 1]
    )
    open_play_xg = model.predict_proba(test_open[FEATURES])[:, 1]
    model_name
    return FEATURES, PENALTY_XG, model, model_name, open_play_xg, test_xg


@app.cell
def _(np, open_play_xg, test, test_open, test_xg):
    from sklearn.metrics import brier_score_loss

    quality = {
        "log loss on open-play shots (compare with the clue table)": round(
            log_loss(test_open["goal"], open_play_xg), 4
        ),
        "brier score on open-play shots (lower is better)": round(
            brier_score_loss(test_open["goal"], open_play_xg), 4
        ),
        "total xG on ALL test shots (penalties count 0.76)": round(
            float(test_xg.sum()), 1
        ),
        "actual goals on those shots": int(test["goal"].sum()),
    }
    quality
    return (quality,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        **Sanity check:** a good xG model's *total* should land near the *actual*
        number of goals. Compare the last two numbers above.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Step 5 - Draw the model's brain

        Let's ask the model "what if?" for every spot on the pitch and paint the
        answers. This is the map TV analysts show when they talk about
        "good shooting positions".
        """
    )
    return


@app.cell
def _(FEATURES, model, np, pitch):
    xs = np.linspace(52.5, 105, 40)
    ys = np.linspace(6, 62, 30)
    grid_x, grid_y = np.meshgrid(xs, ys)

    grid_distance = np.hypot(105 - grid_x, 34 - grid_y)
    grid_angle = np.degrees(
        np.abs(
            np.arctan2(3.66 - (grid_y - 34), 105 - grid_x)
            - np.arctan2(-3.66 - (grid_y - 34), 105 - grid_x)
        )
    )
    import pandas as _pd

    grid_shots = _pd.DataFrame(
        {
            "distance": grid_distance.ravel(),
            "angle": grid_angle.ravel(),
            "is_header": False,
        }
    )
    grid_xg = model.predict_proba(grid_shots[FEATURES])[:, 1].reshape(
        grid_x.shape
    )

    fig3, ax3 = pitch.draw(figsize=(12, 8))
    heat = ax3.pcolormesh(grid_x, grid_y, grid_xg, cmap="Greens", alpha=0.8)
    fig3.colorbar(heat, ax=ax3, label="xG", shrink=0.7)
    ax3.set_title("The model's answer for every spot on the pitch")
    fig3
    return ()


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Step 6 - Your turn

        Build a shot. Move the sliders and watch the model grade it.
        """
    )
    return


@app.cell
def _(mo):
    distance_ui = mo.ui.slider(
        start=1, stop=45, value=11, label="Distance to goal (m)", show_value=True
    )
    angle_ui = mo.ui.slider(
        start=1, stop=150, value=35, label="Angle to goal (degrees)", show_value=True
    )
    header_ui = mo.ui.switch(label="it's a header")
    penalty_ui = mo.ui.switch(label="it's a penalty")
    mo.hstack([distance_ui, angle_ui, header_ui, penalty_ui], justify="start")
    return angle_ui, distance_ui, header_ui, penalty_ui


@app.cell
def _(
    FEATURES,
    PENALTY_XG,
    angle_ui,
    distance_ui,
    header_ui,
    mo,
    model,
    penalty_ui,
    shots,
):
    if penalty_ui.value:
        my_xg = PENALTY_XG
    else:
        import pandas as _pd2

        my_shot = _pd2.DataFrame(
            [
                {
                    "distance": distance_ui.value,
                    "angle": angle_ui.value,
                    "is_header": header_ui.value,
                }
            ]
        )
        my_xg = float(model.predict_proba(my_shot[FEATURES])[:, 1][0])

    league_average = shots["goal"].mean()

    mo.md(
        f"""
        ## Your shot: **{my_xg:.2f} xG**

        Out of 100 shots like yours, about **{my_xg * 100:.0f}** would go in.

        For comparison, an average shot in this dataset scores
        **{league_average * 100:.0f}** times out of 100.
        """
    )
    return ()


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Keep going (challenges)

        1. **Left foot, right foot?** Add `bodyPart == "FOOT_LEFT"` as a clue.
           Does it help or just add noise?
        2. **Find the flukes.** Which goals had xG under 0.05? Find one on
           YouTube and decide: lucky, or is the model missing a clue?
        3. **Best finishers.** Join the shots to the `players` file and ask:
           who scores more than their xG says they should?
        4. **Break it.** Train on the first half of the season, test on the
           second. Does the model still work on matches it has never seen?
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---

        ### Credits

        - **Lesson idea and structure:** inspired by
          [Chris Dove](https://www.linkedin.com/in/chris-dove-7a7b8389/)'s
          (Arsenal FC) NHSSAA Summer Symposium webinar, June 2026. This notebook
          is original code written for NHSSAA - Chris shared the ideas, not his code.
        - **Data:** [Impect Open Data](https://github.com/ImpectAPI/open-data) -
          Bundesliga 2023/24. Data is loaded directly from Impect at runtime and
          stays under their terms of use.
        - **Tools:** [marimo](https://marimo.io), [kloppy](https://kloppy.pysport.org),
          [mplsoccer](https://mplsoccer.readthedocs.io), LightGBM / scikit-learn.
        - **Built by** [NHSSAA](https://www.nhssaa.org) - the National High School
          Sports Analytics Association.
        """
    )
    return


if __name__ == "__main__":
    app.run()
