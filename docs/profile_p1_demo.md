# Three-stakeholder P1 activation: demonstration for the 16 October meeting

## Why this experiment (derived from project documents)

The 8 October PhD follow-up minutes request a multiparty experiment over two data sources, then integration into the Social Data Space. The 16 September notes emphasise first defining **indicator logic, equations and typed columns**, *then* requesting data from Messina, with DS8 (validated household survey) as a practical fallback. They record that using ISEE/DS1 is blocked.

The SOCIAREM vulnerability profile specification describes **P1: structural economic vulnerability** in terms of income (I1), relative poverty (I2), household energy burden (I3), and complementary evidence including payment interruptions/nonpayment (I4). Those sources define the relevant variables, but **do not approve the exact joint P1 activation logic below**.

## Demonstration inputs — THREE private stakeholders

| Party | Data source | Stakeholder simulated | Columns kept private | Indicators |
|---|---|---|---|---|
| P0 | DS8 | Fondazione Messina / competent social entity with audited self-declaration | `annual_equiv_income_cents` | I1/I2; required for I3 |
| P1 | DS4 | Electricity retailer | `annual_electricity_cost_cents`, `payment_incident` (0/1) | Part of I3, I4 |
| P2 | DS14 | Gas/fuel supplier | `annual_non_electric_cost_cents` | Part of I3 |

Household identifiers and row ordering are treated as **already aligned and public** (7 invented households). They are used for local synthetic validation; identifiers are **not part of the MPC secret input**. Real record linkage via PSI is not implemented.

Note the difference between energy expenditure **EUR cents** and energy consumption **kWh**: this prototype computes a financial burden, not kWh consumption.

## Exact experimental rules

Public policy parameters, for demonstration **only**:
- national median annual equivalent income: EUR 18,000 (synthetic illustrative benchmark);
- poverty rule: equivalent income strictly below 60% of that median, hence less than EUR 10,800;
- burden rule: combined annual electricity + non-electric energy expenditure strictly greater than 10% of annual equivalent income (illustrative threshold).

The rule is:
```text
I2 = (100 * income_cents < 60 * 1_800_000)
I3_high = (100 * (electricity_cents + fuel_cents) > 10 * income_cents)
P1_activated = I2 AND I3_high
P1_priority_tier = 0 if not activated
                   1 if activated AND no payment incident
                   2 if activated AND payment incident (I4)
```

The financial burden I3 is computed jointly over three sources; the P1 activation uses I2 and I3, while I4 reinforces prioritisation. `payment_incident` is a binary simplification of I4, which in the taxonomy has richer event-count semantics. **The P1 rule and thresholds require validation by project partners before any operational use.**

The only values revealed by MP-SPDZ are the seven public tiers, not incomes, bills, gas expenses, individual poverty test or individual burden test. A tier-2 output itself can reveal something about payment incidents: SMPC does not eliminate leakage implied by an output.

## Immediate preview (plaintext, already unit-tested)

```bash
python3 scripts/show_profile_p1.py
python3 -m unittest discover -s tests -v
```

Expected tiers for H001..H007:
```text
2 0 0 1 0 2 0
```
Three households activate P1. Two of them are assigned reinforced tier 2.

The preview is **not secure computation**: it merges synthetic records as a plaintext regression oracle. This is suitable for explaining the calculation but not claiming an SMPC deployment.

## Actual 3-party MP-SPDZ experiment (Linux/WSL)

1. Install/build [MP-SPDZ](https://github.com/data61/MP-SPDZ) using its official guide. Compile `semi2k-party.x`; note MP-SPDZ itself is not vendored here.
2. From THIS repository, run `bash scripts/run_profile_p1.sh /absolute/path/to/MP-SPDZ 10`.
3. The runner checks the output of all three protocol parties against the plaintext reference and prints PASS only if they match.

The runner uses 3 *local processes* for P0, P1, P2. A real deployment needs three separate machines/trust domains, individual private file management, authenticated communication, governance enforcement and record alignment. The selected Semi2k protocol assumes **semi-honest** behaviour, not malicious protection.

The optional GitHub Actions workflow `Three-party MP-SPDZ smoke test` attempts to build MP-SPDZ and execute that run on a Linux host. Check its actual status before reporting a cryptographic demonstration as successful; Python baseline passing is insufficient.

## How to present this to Jon and Mikel (2 minutes)

1. Show source-to-stakeholder mappings for DS8 / DS4 / DS14 and typed fields.
2. Explain each household has a different set of private attributes; the P1 rule cannot be evaluated by one institution from its own inputs alone.
3. Explain that the MPC circuit computes I2 and I3, activates P1, and reinforces priority with I4, revealing only a three-value tier.
4. Show the local preview and its regression tests. If the MP-SPDZ run has passed, **also** show the actual 3-party execution with its run log.
5. State candidly that thresholds, record linkage, trust model, and governance integration must be decided before applying this to the Messina pilot.
