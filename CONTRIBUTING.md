# Contributing

Contributions should make the course clearer and more reproducible for AI
Product Managers while preserving the ten-milestone learning sequence.

## Before proposing a change

1. Open an issue describing the learner problem or incorrect behavior.
2. Keep the target audience strictly AI Product Managers.
3. Prefer a concrete product decision, worked example, or inspectable artifact
   over added terminology.
4. Do not broaden this repository into an application or another evaluation
   framework course.

## Local checks

Run setup once, then the fast preflight:

```bash
./scripts/setup_course.sh
./scripts/preflight_course.sh
```

For changes to customer-support evaluation inputs, deliberately regenerate and
review the relevant manifest:

```bash
.venv/bin/python scripts/eval_manifest.py --write
```

Do not regenerate a manifest merely to silence an unexplained mismatch. Do not
run the final-test command as part of routine contribution checks.

## Lesson changes

- Keep the explanation, checkpoint, and completion criterion aligned.
- Update `answer-key/README.md` and the milestone table when a checkpoint changes.
- Teach one distinction at a time and include a useful partial-answer hint.
- Preserve exact version and file references when explaining implementation.
- Mark recorded numeric results as small worked examples rather than general
  performance claims.

## Evaluation changes

- Pin model and dataset revisions.
- Add tests for scorer logic or data contracts when behavior changes.
- Preserve aggregate and per-sample evidence for any accepted baseline update.
- Explain which product claim or failure mode the change is intended to measure.
- Keep development, regression, and final-test roles distinct.

By contributing, you agree that your contribution is licensed under this
repository's MIT License and that you have the right to submit it.
