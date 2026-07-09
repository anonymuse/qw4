# Agent F: Reporting And Publication Templates

## Objective

Create the reporting path that turns Phase 0 run artifacts into a credible technical finding.

## Read First

- `docs/minimum-viable-finding.md`
- `docs/risk-register.md`
- `docs/decisions/ADR-002-phase0-transport-first.md`
- Agent B schemas if available

## Owned Paths

- `tools/report/`
- `docs/findings/`
- `publication/`
- small edits to `README.md` only for links

## Deliverables

Create:

```text
docs/findings/phase0-transport-template.md
publication/writeups/phase0-transport-finding-outline.md
publication/figures/README.md
tools/report/README.md
```

If time allows, create a standard-library report script:

```bash
python3 tools/report/summarize_phase0.py artifacts/runs/<run-id>
```

The report should surface:

- what was measured;
- what hardware path was used;
- why loopback results are not hardware claims;
- latency percentiles;
- throughput by block size;
- checksum failures;
- coordinator overhead;
- remote expert-rate sensitivity;
- go/no-go decision.

## Acceptance Checks

The template is accepted if it can represent both:

- a positive result that justifies model placement work;
- a negative result that becomes the publishable finding.

## Do Not

- Do not write marketing copy.
- Do not claim final model performance.
- Do not hide negative results.
- Do not generate fake hardware results.

## Handoff Notes

Report:

- report template paths;
- any script command;
- schema fields needed from Agent B or C;
- missing plots or tables.

