# Threat model (experimental v0)

**Parties.** Party 0 owns annual energy expenditure; party 1 owns annual equivalent income. Records are pre-aligned in a public, consistent household order. Both sites run MP-SPDZ locally in the demo; this is not network isolation.

**Security goal.** Use a two-party SMPC protocol under a **semi-honest (honest-but-curious)** assumption: parties follow the protocol but try to infer each other's inputs. The permitted leakage is the number/order of households, the public threshold, and one classification bit per household. Intermediate and raw values must remain hidden according to the selected protocol's assumptions.

**Not guaranteed.** The public output can reveal information about an individual's values (especially under repeated thresholds). There is no protection against maliciously crafted inputs, collusion with external actors, misalignment of records, compromised hosts, repeat-query inference, denial of service, or legal/compliance failures. Neither a reproducible local benchmark nor these synthetic data demonstrates GDPR compliance.

**Pilot assumptions.** Synthetic fixtures only; no real identities, no cross-institutional linkage, no PSI, no EDC connectors. Input owners must be isolated for a realistic deployment. An approved output recipient, query limits, policy enforcement, authentication, and PSI/record alignment are future design tasks.
