# Onboarding experiment check

Take-home analysis of last month's onboarding A/B test. Leadership saw a better overall conversion rate on the new flow and wanted to ship it. The file does not support a clean global rollout.

This repo is the writeup plus the script that produces every number and chart. The raw `experiment_results.csv` is **not** included (the assignment asked not to submit it). Drop the CSV in `data/` or pass `--csv`.

## What is in the file

14,000 users who went through signup.

| column    | meaning |
|-----------|---------|
| user_id   | unique user |
| segment   | how they found the product: organic, paid_search, referral, app_store, influencer |
| variant   | control (old flow) or treatment (new flow) |
| converted | 1 if they finished signup, else 0 |

## How to run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# put experiment_results.csv somewhere, then:
python analyze.py --csv path/to/experiment_results.csv
```

That prints the tables, writes `answers.json`, and refreshes the PNGs in `figures/`.

## Outputs

- `ANSWERS.md` — the actual submission writeup
- `answers.json` — the numeric fields requested for fact-checking
- `analyze.py` — validation, lifts, mix-adjusted number, CIs, plots
- `figures/`
  - `01_overall_conversion.png`
  - `02_segment_conversion.png`
  - `03_segment_lift.png`
  - `04_segment_allocation.png`
  - `05_mix_adjusted_contribution.png`

## Result in one paragraph

Naive lift is +6.61 pp (19.82% control vs 26.43% treatment; 7,136 vs 6,864 users). Treatment is stacked with organic traffic and control is stacked with paid search, and those two channels have very different baselines. Weighting each segment's own lift by its share of all users brings the overall number down to +1.63 pp. The only segment I would treat as a real positive effect is app_store (+11.24 pp). Influencer's -6.74 pp sits on 250 users and a CI that crosses zero. Organic and paid_search assignment is far from 50/50 and should be checked before anyone ships.

## Method

Conversion rate = conversions / users in that cell. Lift is always treatment minus control, in percentage points. Mix-adjusted lift uses each segment's share of the full 14,000, not the share of treatment. Intervals are unpooled two-proportion CIs.

## Limits

One CSV. No assignment log, no timestamps, no secondary metrics. The imbalance could be a bug, a staged rollout, or a flag rule. The file cannot tell which.
