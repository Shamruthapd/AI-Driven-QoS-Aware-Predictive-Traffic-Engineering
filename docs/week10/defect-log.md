# Week 10 — Integration Defect Log

## Rules
Log observed defects and confirmed integration blockers. Assign an owner, preserve reproduction evidence, and retest after each fix. Do not present an unverified assumption as a confirmed defect.

| ID | Run/date | Defect or blocker | Evidence/reproduction | Owner | Status | Fix/retest |
|---|---|---|---|---|---|---|
| D-001 | Pending | Live AI/controller interface and unified event flow require verification | Week 9 AI runtime reads processed CSV; this alone does not establish live controller-to-AI exchange | Member 1 + Member 4 | OPEN — verify | Agree interface schema, transport, IDs, and timeouts; test end-to-end |
| D-002 | Pending | Integrated congestion and link-failure recovery have not been evidenced here | Requires coordinated S2/S3 runs and enforcement evidence | Member 3 + Member 4 | OPEN — verify | Run scenarios and attach logs and measurements |
| D-003 | Pending | End-to-end delay measurement is pending | Requires correlated telemetry, prediction, decision, and enforcement timestamps | Member 4 + component owners | OPEN — verify | Capture timestamps and calculate delay |

## Additional defects
Add rows for each observed failure. Include the scenario, reproduction steps, log path, impact, owner, fix, and retest result.

Close a defect only after a successful retest is documented.
