# Calcium-Score-Agent

Automated weekly intelligence for people living with a **very high coronary artery calcium (CAC) score** (including CAC > 600).

This repository contains:

- A **baseline guidance brief** for what to avoid, what to prioritize, and how to discuss treatment intensity with a clinician.
- A **weekly research agent** that scans newly indexed PubMed studies on CAC, plaque progression/regression, lipid-lowering therapy, inflammation, and emerging plaque-targeted science.
- A **GitHub Actions workflow** that runs weekly and writes a timestamped report.

## Medical safety note

This project is educational and not a diagnosis or treatment plan. A CAC score > 600 is generally high-risk territory and warrants clinician-guided management.

## Repository layout

- `docs/baseline-guidance-cac-over-600.md` - evidence-based baseline recommendations.
- `scripts/weekly_cac_agent.py` - weekly updater script.
- `reports/weekly/` - generated weekly report files.
- `reports/latest.md` - latest generated report.
- `.github/workflows/weekly-cac-update.yml` - weekly automation.

## Local usage

Run the weekly agent manually:

```bash
python3 scripts/weekly_cac_agent.py
```

Generate output at a specific path:

```bash
python3 scripts/weekly_cac_agent.py --output reports/weekly/2026-03-23.md
```

Also refresh `reports/latest.md`:

```bash
python3 scripts/weekly_cac_agent.py --update-latest
```

## What the weekly report includes

1. Safety-first context for CAC > 600
2. Practical "avoid / prioritize" checklist
3. New PubMed studies from the past week grouped by topic
4. Ongoing and emerging plaque-modifying research watchlist
