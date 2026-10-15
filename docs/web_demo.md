# Interactive P1 research demo — meeting guide

**Status:** web server + animated browser frontend implemented; API integration and frontend syntax checks passed in GitHub Actions. Separate 3-party MP-SPDZ integration workflow has also passed. This is a demonstrator with **invented** household records; it is not production infrastructure.

## Quick demo on Windows (no setup other than Python and Git)

1. Clone once (or `git pull` if already cloned):

   ```powershell
   git clone https://github.com/rubenl-cloud/smpc-institutional-scoring.git
   cd smpc-institutional-scoring
   ```
2. Run:

   ```powershell
   python web/server.py
   ```

3. Open **http://127.0.0.1:8765**. No external web hosting, npm, Docker, Python packages or database required for this mode.

If `python` isn't recognized, use `py -3 web/server.py`. Leave that terminal open throughout the demo. Ctrl+C to stop it.

## Screen walkthrough (2–4 minutes)

1. Explain the stakeholder cards: DS8 = social organisation with equivalent household income; DS4 = electricity retailer with expenditure + payment incident; DS14 = non-electric fuel provider with costs.
2. Select **H001**. Without clicking "Show synthetic inputs", attribute values are represented as private. Click **Show synthetic inputs** to disclose intentionally fabricated data *for education only*.
3. Click **Run visual reference**. Animated lines represent the flow of the conceptual calculation, but **this mode is a server-side plaintext oracle**, not an MPC protocol. Observe `P1_TIER 2` for H001.
4. Click H004: `P1_TIER 1`, demonstrating activation without recorded payment incident. Click H005 or H007: `P1_TIER 0`, demonstrating strict threshold boundaries.
5. Change the burden threshold to 20%; the reference will recompute; none of the demo households activate at this higher threshold.
6. Point to **I2 / I3 / I4**, distinguishing activation rules from the payment incident used only to reinforce severity.
7. Click the **3-party CI verified** link for evidence of a successfully executed independent *integration test* with MP-SPDZ. If local MP-SPDZ is configured, use the **Run actual 3-party MPC** button for a live, cryptographic run.

### What the colours/lines mean

The UI has three visually separated synthetic **data owners**, a joint computation layer, and the disclosed **P1 tier**. In real MP-SPDZ, parties exchange secret shares and protocol messages, **not raw incomes and bills**. The browser animation is educational: it does not depict every protocol message, and is not proof that a live protocol ran.

## Live 3-party cryptographic mode on Linux / WSL

Install an upstream MP-SPDZ checkout **outside** this repository. A recent Ubuntu toolchain and `semi2k-party.x` are required. Our [GitHub Actions integration workflow](../.github/workflows/three-party-smpc.yml) installs the dependencies, builds and executes it in Linux, and validates the final tiers. That workflow is a useful reproducible reference for building MP-SPDZ.

An outline for an Ubuntu/WSL machine:

```bash
sudo apt-get update
sudo apt-get install -y automake build-essential clang cmake git libboost-dev libboost-filesystem-dev libboost-iostreams-dev libboost-thread-dev libgmp-dev libntl-dev libsodium-dev libssl-dev libtool python3
git clone --recurse-submodules https://github.com/data61/MP-SPDZ.git ~/MP-SPDZ
cd ~/MP-SPDZ
make setup
make -j2 semi2k-party.x
cd /path/to/smpc-institutional-scoring
export MP_SPDZ_HOME="$HOME/MP-SPDZ"
python3 web/server.py
```

Now load http://127.0.0.1:8765. The second button should be enabled. It invokes the actual MP-SPDZ 3-party runner with the same public thresholds selected in the UI; the process prints one tier per household, which the backend compares with the independent Python reference. It **does not** silently run a plaintext fallback.

The Web server stays on **127.0.0.1**. It was not designed for Internet hosting. A live run uses three MPC processes on the **same machine** and a test harness that reads the three invented CSVs. This is enough to validate the protocol calculation, but not isolation of private institutional records. Hosting public internet endpoints or processing real personal records requires a separate security and architecture review.

## Security and methodological boundaries

- P1 means Structural Economic Vulnerability. Income I1 / relative poverty I2 and burden I3 underpin the demo; I4, represented by a simplified yes/no payment incident instead of a frequency, reinforces priority.
- The median annual equivalent income of EUR 18,000 is **synthetic**, not a real statistical assertion. A 60% poverty threshold derives from indicator I2; the 10% energy burden trigger and the AND activation rule are **illustrative design choices** requiring expert approval.
- All seven records are fictional; their indices are pre-aligned among participants. There is no PSI, no consent management, no formal ODRL contract negotiation, no Eclipse EDC connector, no actual energy-community eligibility decision.
- Output tiers may themselves leak sensitive correlations (e.g. tier 2 strongly correlates with nonpayment); the protocol protects the inputs according to its *semi-honest* model, not against arbitrary inference from repeated permitted outputs.
- The public synthetic preview, web API and Python oracle handle data in plaintext by design. **Only a successful /api/mpc invocation or the previously passing 3-party CI run can be cited as actual MP-SPDZ SMPC execution.**

## Validation

```sh
python -m unittest discover -s tests -v
node --check web/app.js
```

Node is needed only for the optional syntax validation, **not** to run the web dashboard.

- Python checks: [GitHub Actions](https://github.com/rubenl-cloud/smpc-institutional-scoring/actions/workflows/python-reference.yml)
- Web API checks: [GitHub Actions](https://github.com/rubenl-cloud/smpc-institutional-scoring/actions/workflows/web-checks.yml)
- Secure 3-party SMPC integration: [GitHub Actions](https://github.com/rubenl-cloud/smpc-institutional-scoring/actions/workflows/three-party-smpc.yml)

## Next engineering steps

1. Validate final indicator/profile rules with SOCIAREM domain partners.
2. Make source-specific party startup and storage independent across distinct trust domains.
3. Add private household record alignment (PSI) and policy-controlled output approval.
4. Place orchestrator/credentials/agreements under EDC governance before any real pilot use.
