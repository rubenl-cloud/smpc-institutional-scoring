# Simple editable web demonstration

## Start immediately on Windows

From the repository root:

```powershell
python web/server.py
```

Open http://127.0.0.1:8765. No package installation, npm command or database is required.

## Meeting walkthrough

1. Choose one of the seven invented households.
2. Point out the three columns: P0 income, P1 electricity and impago, P2 other energy expenditure.
3. Change any number directly. There are no sliders and no decorative protocol animation.
4. Explain the public 10% I3 threshold and the equation `45·I2 + 40·I3 + 15·I4`.
5. Press **Calcular referencia Python**. The result shows activation, score and the three binary indicators. State clearly that this mode is plaintext.
6. If MP-SPDZ is configured in WSL/Linux, press **Ejecutar MP-SPDZ real**. This mode opens only activation and score, so the indicator boxes say “no revelado”.

The two buttons are intentionally separate. Failure or absence of MP-SPDZ never triggers a hidden plaintext fallback.

## Enable the cryptographic run in WSL/Linux

Build `semi2k-party.x` in an upstream MP-SPDZ checkout, then:

```bash
export MP_SPDZ_HOME=/absolute/path/to/MP-SPDZ
python3 web/server.py
```

The server creates three temporary owner-specific CSV files from the edited synthetic values. The runner converts them into MP-SPDZ files with prefix `<temporary>/inputs/Input`, and `semi2k-party.x` receives that location through `-IF`. Temporary files are deleted after success or failure.

This improves reproducibility and avoids overwriting repository fixtures. It does not create real institutional isolation because one local server still prepares all three files.

## Verification

```sh
python -m unittest discover -s tests -v
node --check web/app.js
```

The Python suite checks boundaries, weights, generated owner files, transcript parsing, editable API inputs, static assets and the absence of a plaintext fallback. The real protocol requires either a local WSL/Linux run or a passing `Three-party MP-SPDZ smoke test` workflow.
