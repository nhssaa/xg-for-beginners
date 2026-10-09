# xG for Beginners

**NHSSAA Lesson 1: build your first expected-goals (xG) model from 8,000+ real Bundesliga shots.**

xG is the number you hear on TV: "that shot was 0.35 xG." In this lesson you build
that number yourself - starting from raw event data, adding one clue at a time
(distance, angle, header, penalty), and finishing with the same kind of model
pro clubs use. Everything runs for free, in your browser, with nothing to install.

*Inspired by Chris Dove's (Arsenal FC) NHSSAA Summer Symposium webinar (June 2026).
All code here is original, written for the NHSSAA community.*

## Run it in one click

**Preview the lesson (outputs included, no login):**

https://molab.marimo.io/github/nhssaa/xg-for-beginners/blob/main/notebooks/xg_for_beginners.py

**Run it live in your browser (no login, nothing to install):**

https://molab.marimo.io/github/nhssaa/xg-for-beginners/blob/main/notebooks/xg_for_beginners.py/wasm

[![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/nhssaa/xg-for-beginners/blob/main/notebooks/xg_for_beginners.py)

In the browser, keep the "Matchdays to load" slider small (1-3). Each matchday is
~50 MB downloaded straight from Impect. To train on the full season
(34 matchdays, 8,069 shots), run it on a computer instead - see below.

## Run it on your own computer

```bash
pip install -r requirements.txt
marimo edit notebooks/xg_for_beginners.py
```

(Or with [uv](https://docs.astral.sh/uv/): `uv run --with-requirements requirements.txt marimo edit notebooks/xg_for_beginners.py`)

Slide "Matchdays to load" to 34 for the full season. Locally the notebook trains
with **LightGBM** (the library from the webinar); in the browser it automatically
uses scikit-learn's equivalent, because LightGBM can't run inside a browser tab.

## The lesson arc

1. **Get the data** - pull real Bundesliga 2023/24 shots from Impect Open Data.
2. **Meet a shot** - where was the shooter, foot or head, did it go in?
3. **Clue 1: distance** - closer is better, but by how much?
4. **Clue 2: angle** - same distance, very different shot.
5. **Clue 3: headers** - same spot, harder skill.
6. **Clue 4: penalties** - special situation, hard-coded at 0.76.
7. **The real model** - gradient-boosted trees (LightGBM), and an honest check
   of when fancy models actually help.
8. **Your turn** - interactive sliders: build a shot, get its xG.
9. **Challenges** - left foot vs right foot, find the flukes, best finishers.

## Repo layout

```
notebooks/xg_for_beginners.py   # the lesson (marimo notebook)
scripts/build_dataset.py        # regenerate the shots dataset with kloppy
requirements.txt                # local dependencies
LICENSE                         # MIT (our code)
```

## About the data (please read)

The notebook downloads data **directly from
[Impect Open Data](https://github.com/ImpectAPI/open-data)** at runtime.
Using that data means accepting
[Impect's terms of use](https://github.com/ImpectAPI/open-data/blob/main/LICENSE.pdf),
which allow learning/research use with credit - and do not allow redistributing
the data. That is why this repo intentionally contains **no dataset**: everyone
pulls it from the source themselves. Data credit: **Impect**.

## For NHSSAA chapters and students

- Work in **your own GitHub account**. Experiment, break things, learn.
- When something is finished, we host a **copy** in this org (with you credited)
  so other chapters can learn from it. Ask your chapter lead or email
  admin@nhssaa.org to submit finished work.
- This org never hosts student personal data. Finished, public-ready work only.
  (Conference registration data lives elsewhere, never here.)

## Credits

- Lesson idea and structure inspired by **Chris Dove** (Arsenal FC), NHSSAA
  Summer Symposium webinar, June 2026. He shared the ideas, not his code.
- Data: [Impect Open Data](https://github.com/ImpectAPI/open-data) (Bundesliga
  2023/24, ~8,069 shots).
- Tools: [marimo](https://marimo.io), [kloppy](https://kloppy.pysport.org),
  [mplsoccer](https://mplsoccer.readthedocs.io), LightGBM / scikit-learn.
- Built by [NHSSAA](https://www.nhssaa.org) - the National High School Sports
  Analytics Association, a 501(c)(3) teaching high-schoolers sports analytics.
