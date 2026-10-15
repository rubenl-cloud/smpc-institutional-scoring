# Three-stakeholder Profile 1 activation and weighted score

## Purpose

The project definition associates Profile 1 with structural economic vulnerability and the indicators I2 (relative poverty), I3 (household energy burden) and I4 (payment interruption/non-payment). This demonstration turns those concepts into a small, auditable experiment. It does not claim that the resulting rule has been approved by SOCIAREM partners.

## Private synthetic inputs

| Party | Simulated stakeholder | Private fields |
|---|---|---|
| P0 / DS8 | social organisation | annual equivalent income |
| P1 / DS4 | electricity retailer | annual electricity cost; payment incident 0/1 |
| P2 / DS14 | gas/fuel provider | annual non-electric energy cost |

All amounts use integer euro cents inside Python and MP-SPDZ. Household identifiers and row order are assumed to be already aligned and are not secret inputs. PSI is not implemented.

## Exact experimental rule

Public defaults:

- median annual equivalent income: EUR 18,000;
- relative-poverty threshold: 60% of the median;
- high energy-burden threshold: strictly more than 10% of income;
- weights: I2 = 45, I3 = 40, I4 = 15.

```text
I2 = 100 × income < 60 × median
I3 = 100 × (electricity + other energy) > 10 × income
I4 = payment incident, encoded as 0 or 1

P1_active = I3
P1_score  = P1_active × (45×I2 + 40×I3 + 15×I4)
```

I3 is the activation condition requested for the experiment. I2 has the largest weight because it represents the structural economic component. I3 contributes 40 points and is always one when the profile is active. I4 contributes 15 points as a reinforcement of urgency. If I3 does not cross the strict threshold, the score is zero.

For H001..H007 with the repository fixtures, the expected scores are:

```text
100 40 0 85 0 100 55
```

Five of the seven invented households activate the profile.

## What each execution proves

`python scripts/show_profile_p1.py` uses the plaintext oracle. It can display I2, I3 and I4 because it intentionally sees all invented values. It proves only that the formula behaves as specified.

`bash scripts/run_profile_p1.sh /path/to/MP-SPDZ` generates separate temporary input files, compiles the secure program and runs three local Semi2k processes. The MPC program opens only:

```text
P1_ACTIVE <0-or-1> P1_SCORE <0-to-100>
```

The runner compares those outputs with the plaintext oracle and prints `PASS` only on exact equality. The temporary data and generated source are removed at exit.

The output score can reveal combinations of the binary indicators. This is intentional for the demonstration and must be analysed before a real release policy is chosen.

## Honest limitations to state in a meeting

- All records are synthetic.
- The web server is a shared local test harness and can see the edited inputs.
- The three parties are local processes, not isolated institutions.
- Semi2k is being evaluated under a semi-honest model.
- PSI/private record linkage, independent data ingestion, governance and Eclipse EDC integration are pending.
- The thresholds and weights require domain and partner validation.

## Suggested one-minute explanation

“Three institutions own different attributes of the same synthetic household. I3 activates Profile 1 when combined energy expenditure exceeds 10% of income. Once active, a linear model assigns 45 points for relative poverty, 40 for high energy burden and 15 for a payment incident. Python gives us an understandable reference. MP-SPDZ evaluates the same comparisons and equation on secret-shared inputs and opens only the activation bit and final score. In this prototype the parties are three processes on one computer, so it demonstrates the cryptographic calculation but not yet a real institutional deployment.”
