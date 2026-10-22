# Member 4 — Week 9 bundle

This is a proposed Week 9 addition for the existing project repository. It is intentionally limited to Member 4's role: AI runtime, model inference safety, and experiment parsing/summary. It does not claim that Mininet/OS-Ken integration or team end-to-end validation has passed.

## Files to copy into the project root

- `ai-model/ai_loop.py`
- `scripts/evaluate.py`
- `config/ai_loop.yaml`
- `docs/week9/ai-runtime-and-harness.md`
- `tests/test_ai_loop.py`
- `tests/test_evaluate.py`
- `tests/fixtures/week8_qos_on_vs_off_measurements.csv` (only a test fixture; not production data)

If working from a repository clone, copy the folder contents into the existing root and preserve existing files. Do not replace your existing Week 8 data or scripts.

## Commands (PowerShell from repository root)

```powershell
python -m py_compile ai-model/ai_loop.py scripts/evaluate.py
python -m unittest discover -s tests -v
python ai-model/ai_loop.py --once
python ai-model/ai_loop.py --no-model --interval 1 --duration 5
python scripts/evaluate.py --week8-summary data/results/week8_qos_on_vs_off_measurements.csv
```

The one-cycle command expects the configured model checkpoint and scaler. The no-model command tests graceful loop behavior in a smoke test only. Run the model-backed loop for 30 minutes in the actual project environment before claiming the 30-minute requirement has passed.

## Week 8 evidence caveat

The inspected repository has `data/results/week8_qos_on_vs_off_measurements.csv` and the derived analysis CSV but does not have the original Week 8 iPerf3 JSON inputs in the committed tree. The `--week8-summary` option recalculates ON/OFF comparisons from that summary CSV. That is a summary-level consistency check, not raw-file reproduction. To satisfy the original plan exactly, recover the original JSON files and pass those files through the raw-file harness.

## Suggested commit

```powershell
git add ai-model/ai_loop.py scripts/evaluate.py config/ai_loop.yaml docs/week9/ai-runtime-and-harness.md tests/test_ai_loop.py tests/test_evaluate.py tests/fixtures/week8_qos_on_vs_off_measurements.csv
 git status --short
 git commit -m "feat(week9): add resilient AI runtime and evaluation harness"
 git push origin main
```

Review `git status` first and include only files you intend to commit.
