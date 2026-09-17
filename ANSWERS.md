# Onboarding Experiment Investigation

Growth shipped a new onboarding flow to a random subset of last month's signups. Leadership wants to roll it out because the overall conversion rate looks better in treatment. This note is the sanity check: what the file actually shows, where the lift is coming from, and what I would not ship on the basis of the topline alone.

Data: `experiment_results.csv`, one row per user (user_id, segment, variant, converted).

---

## Executive summary

The naive overall lift is real in the file: treatment converts at 26.43% vs 19.82% for control, a **+6.61 pp** gap (7,136 control, 6,864 treatment).

That gap is not a clean estimate of "the new flow is better for everyone." Treatment and control do not have the same mix of acquisition sources. Organic users (high baseline conversion, ~35%) are heavily over-represented in treatment. Paid search users (low baseline conversion, ~15%) are heavily over-represented in control. Once you hold the traffic mix fixed and weight each segment's own lift by that segment's share of all 14,000 users, the overall lift drops to **+1.63 pp**.

The only segment where I would claim a meaningful positive effect is **app_store** (+11.24 pp, reasonably large and balanced sample, CI well above zero). Referral is directionally positive but the CI still includes a small negative. Influencer looks bad on the point estimate, but the sample is only 250 users and the CI crosses zero. Organic and paid_search are flat.

I would not roll the new flow out to everyone based on the +6.61 pp headline. I would investigate the assignment imbalance first, then consider an app_store-only rollout (or a holdout) while watching the other channels.

---

## Data validation

Checked before any lift calculation:

- 14,000 rows, 4 columns matching the spec: user_id, segment, variant, converted
- 0 missing values
- 14,000 unique user_ids (no duplicates)
- segment values: app_store, influencer, organic, paid_search, referral
- variant values: control, treatment only
- converted is binary {0, 1}
- user_id range 100001-114000, which is consistent with 14,000 distinct ids
- control 7,136 + treatment 6,864 = 14,000
- conversions: 1,414 control + 1,814 treatment = 3,228 total

Nothing in the file looks corrupt. The odd thing is not dirty data. It is how variants are allocated inside organic and paid_search.

---

## Q1. Overall (naive) difference

| Variant   | Users | Conversions | Conversion rate |
|-----------|------:|------------:|----------------:|
| Control   | 7,136 | 1,414       | 19.8150%        |
| Treatment | 6,864 | 1,814       | 26.4277%        |

Naive lift = 26.4277% - 19.8150% = **+6.6127 percentage points**.

That is a difference in rates, not a relative lift. Relative to control the treatment rate is about 33% higher (6.61 / 19.82), but the assignment asks for percentage points, so +6.61 pp is the number that matters here.

Unpooled 95% CI on the overall difference: roughly +5.22 pp to +8.01 pp. The naive gap is not a small-sample fluke. The question is whether it is measuring the flow or measuring a different mix of users.

![Overall conversion](figures/01_overall_conversion.png)

---

## Q2. Same comparison by segment

Rates below use conversions / users in that cell. Lift is treatment CR minus control CR, in percentage points.

| Segment     | Control N | Control CR | Treatment N | Treatment CR | Lift (pp) |
|-------------|----------:|-----------:|------------:|-------------:|----------:|
| app_store   | 925       | 8.76%      | 960         | 20.00%       | +11.24    |
| influencer  | 119       | 23.53%     | 131         | 16.79%       | -6.74     |
| organic     | 1,298     | 35.29%     | 2,917       | 35.07%       | -0.21     |
| paid_search | 3,353     | 15.18%     | 1,459       | 14.39%       | -0.79     |
| referral    | 1,441     | 23.46%     | 1,397       | 26.27%       | +2.81     |

Exact cell counts used:

- app_store: 81/925 vs 192/960
- influencer: 28/119 vs 22/131
- organic: 458/1,298 vs 1,023/2,917
- paid_search: 509/3,353 vs 210/1,459
- referral: 338/1,441 vs 367/1,397

![Segment conversion rates](figures/02_segment_conversion.png)

**Segment I would not trust: influencer.**

The point estimate looks like a -6.74 pp hit, which is the most dramatic negative number in the table. I would not act on it. The segment is 250 users total (119 control, 131 treatment). The unpooled 95% CI is about **-16.69 pp to +3.22 pp**. That interval crosses zero. A two-sided normal test gives p ~ 0.18. The data is compatible with a real drop, with no change, and even with a small gain. Calling this "treatment hurts influencer users" would be overstating what 22 vs 28 conversions can tell you.

![Segment lifts with 95% CIs](figures/03_segment_lift.png)

---

## Q3. Mix-adjusted overall lift

Weight each segment's own lift by that segment's share of the full 14,000 users (not by how many of that segment landed in treatment).

segment share = n_segment / 14,000
mix-adjusted lift = sum (share_s * lift_s)

| Segment     | N     | Population share | Segment lift | Contribution |
|-------------|------:|-----------------:|-------------:|-------------:|
| app_store   | 1,885 | 13.46%           | +11.2432 pp  | +1.514 pp    |
| influencer  | 250   | 1.79%            | -6.7355 pp   | -0.120 pp    |
| organic     | 4,215 | 30.11%           | -0.2148 pp   | -0.065 pp    |
| paid_search | 4,812 | 34.37%           | -0.7870 pp   | -0.271 pp    |
| referral    | 2,838 | 20.27%           | +2.8146 pp   | +0.571 pp    |
| **Total**   | 14,000| 100%             |              | **+1.63 pp** |

Exact sum of contributions: **+1.6289 pp**, reported as **+1.63 pp**.

![Mix-adjusted contributions](figures/05_mix_adjusted_contribution.png)

Why this is so different from Q1 (+6.61 pp vs +1.63 pp):

The naive comparison treats the two columns as if they were the same population, randomly split. They are not. Treatment is loaded with organic users (2,917 of 4,215 organic users, about 69% of that segment). Control is loaded with paid search (3,353 of 4,812 paid search users, about 70% of that segment). Organic already converts at ~35% under the old flow. Paid search converts at ~15% under the old flow. So a big piece of the +6.61 pp is "treatment happened to contain more of the high-converting channel," not "the new flow raised conversion by 6.61 pp for a typical new user."

The mix-adjusted number answers a different question: if the traffic mix stayed at the overall population shares, and each segment kept the lift we observed inside that segment, what would the overall lift be? About 1.63 pp, and most of that 1.63 comes from app_store.

This does not by itself prove the experiment is invalid. It does mean the headline is not a within-user-type effect.

---

## Q4. Is there a segment with a real, meaningful positive effect?

**app_store.**

Evidence that convinced me, in order:

1. Size of the effect. 81/925 = 8.76% in control vs 192/960 = 20.00% in treatment. That is +11.24 pp, which is large relative to the control baseline in this channel (the rate more than doubles).
2. Sample. 1,885 users, split 925 / 960. Not a tiny cell.
3. Uncertainty. Unpooled 95% CI is about **+8.13 pp to +14.36 pp**. The lower bound is still a clearly positive lift.
4. A two-sided unpooled z-test is around z = 7.07, p ~ 1.57e-12. Even allowing for looking at five segments, this is not an effect that appears because we sliced the data.
5. Assignment inside this segment is close to even (49.1% / 50.9%), so the app_store comparison is not the one being warped by mix.

Referral is the only other positive point estimate (+2.81 pp). I would not call it conclusive. CI is about -0.37 pp to +5.99 pp, p ~ 0.083. Worth watching, not enough to hang a rollout on.

Organic and paid_search are essentially zero. Influencer is noisy, as above.

I am not claiming the CSV proves causality in the strict sense. We do not have the assignment log, timestamps, or a guarantee that a user could not see both flows. What I am claiming is: among the comparisons this file can support, app_store is the only one that looks like a real, meaningful improvement.

---

## Q5. Assignment fractions by segment

| Segment     | Control share | Treatment share | N     |
|-------------|--------------:|----------------:|------:|
| app_store   | 49.07%        | 50.93%          | 1,885 |
| influencer  | 47.60%        | 52.40%          | 250   |
| organic     | 30.79%        | 69.21%          | 4,215 |
| paid_search | 69.68%        | 30.32%          | 4,812 |
| referral    | 50.78%        | 49.22%          | 2,838 |
| Overall     | 50.97%        | 49.03%          | 14,000|

Overall looks like a coin flip. Inside the two largest channels it does not.

![Assignment mix by segment](figures/04_segment_allocation.png)

A chi-square test of segment vs variant is huge (chi-square ~ 1364 on 4 df). That is not a surprise once you look at the table. Something systematically sent organic users toward treatment and paid search users toward control.

Possible explanations I cannot distinguish from this file alone:

- Intentional stratification or a staged rollout that opened treatment first on organic traffic
- A feature-flag rule tied to acquisition source (or to a property correlated with it)
- A mid-experiment change in traffic allocation
- A filtering / logging issue so some control or treatment users in those channels never landed in the export
- An actual randomization / config bug

I am not going to write "the randomization is broken" as a fact. I will write that if the design was supposed to be 50/50 inside every segment, this is off, and someone should pull the assignment config before anyone ships the new flow globally. The mix problem in Q3 is exactly this imbalance showing up in the topline.

---

## Uncertainty notes

Method for intervals: unpooled standard error

SE = sqrt( p_c(1-p_c)/n_c + p_t(1-p_t)/n_t )

95% CI = lift +/- 1.96 * SE

| Segment     | Lift (pp) | 95% CI (pp)       | p-value   |
|-------------|----------:|-------------------:|----------:|
| overall     | +6.61     | [+5.22, +8.01]     | << 0.001  |
| app_store   | +11.24    | [+8.13, +14.36]    | 1.6e-12   |
| influencer  | -6.74     | [-16.69, +3.22]    | 0.18      |
| organic     | -0.21     | [-3.34, +2.91]     | 0.89      |
| paid_search | -0.79     | [-2.96, +1.39]     | 0.48      |
| referral    | +2.81     | [-0.37, +5.99]     | 0.083     |

These are descriptive intervals on the observed conversion difference. They assume independent Bernoulli outcomes and ignore multiple comparisons except as a reason to be conservative about referral and influencer. They do not fix a broken assignment mechanism if one exists.

Practical vs statistical: app_store is both. Referral is neither clearly significant nor huge. A 0.2 pp movement in organic is not something I would spend product time on even if the sample were larger.

---

## Limitations

This CSV cannot tell us:

- how users were randomized, or whether they were
- the intended allocation ratio by segment
- experiment start / end, or whether allocation changed mid-flight
- whether a user could see both flows
- other guardrails (time-to-convert, retention, payment, support tickets)
- downstream revenue, so a conversion lift in app_store could still be a worse business outcome

Until the assignment imbalance is explained, I would treat the naive +6.61 pp as a mix artifact plus a real app_store effect, not as the number to put in a launch email.

---

## Recommendation

1. Do not roll the new flow out to 100% of traffic on the basis of the topline.
2. Ask eng / growth ops why organic is ~70% treatment and paid search is ~70% control.
3. If assignment checks out, ship or expand the new flow for **app_store** and keep a holdout.
4. Leave influencer alone until there is more data. The -6.74 pp number is not decision-quality.
5. Recalculate the global number with a mix-adjusted or stratified estimator going forward, so this mix trap does not happen again.

---

## Investigation process

- Loaded the CSV, checked shape, dtypes, nulls, duplicate user_ids, allowed values for segment / variant / converted.
- Confirmed 14,000 unique users and that segment x variant counts sum back to the totals.
- Computed overall conversion and the naive pp lift. Matched 7,136 / 6,864 and 1,414 / 1,814.
- Built the full segment x variant table. This is where the story changed: app_store jumps, organic and paid_search do not.
- Looked at treatment share within each segment. Organic / paid_search imbalance is obvious from the raw counts, before any test.
- Computed the mix-adjusted lift using population shares as specified. Landed on +1.63 pp. Cross-checked by adding the five contribution terms.
- Added unpooled CIs so I had a way to talk about influencer vs app_store without hand-waving.
- Checked whether a pooled two-proportion test would change the call. It does not. app_store stays tiny-p, influencer stays not significant.
- Briefly considered a relative-lift view. Rejected it as the main answer because the assignment asks for percentage points and baselines differ a lot by segment.
- Thought about Simpson's paradox framing. Useful as intuition, but the mix-adjusted formula in Q3 is the actual number they asked for, so that is what I reported.
- Did not chase per-user_id patterns or "maybe converted is mislabeled." Nothing in the file suggested that.
- Did not fit a logistic regression with segment x variant interactions. The 2x2 tables already give the same conclusion and are easier to defend live.

---

## How the numbers were produced

All counts and rates come from `analyze.py` (pandas groupby on the raw CSV). Formulas:

```
CR = conversions / users
lift_pp = 100 * (CR_treatment - CR_control)
share_s = n_s / 14000
mix_adjusted_pp = 100 * sum(share_s * (CR_t_s - CR_c_s))
```

Re-run:

```
python analyze.py --csv /path/to/experiment_results.csv
```
