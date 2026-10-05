# Milestone 10: Reproducible evaluation workflow

## Goal

Make an evaluation repeatable and auditable from a clean checkout. Another
person should be able to identify every input to a run, recreate the environment,
rerun the regression evaluation, and explain any permitted source of variation.

The identity of an evaluation is broader than its command:

```text
code commit
+ dependency lock
+ model repository and immutable revision
+ task, prompt, scorer, and dataset contents
+ run configuration and seeds
= reproducible run identity
```

The result JSON and per-sample JSONL are evidence produced by that identity.
Model, dataset, request, and response caches are performance optimizations; they
are not evidence and must not be required to reproduce a run.

## Initial audit and resolution

This was the audit before Milestone 10 implementation. The final column records
how each gap was closed.

| Area | Initial state | Resolution |
|---|---|---|
| Python dependencies | `uv.lock` existed and `lm_eval[hf]==0.4.13` was pinned | A temporary clean clone now recreates `.venv` from the frozen lockfile |
| Models | Pythia and Qwen configurations pinned immutable Hugging Face revisions | The selected Qwen revision is enforced by the manifests and result checker; availability still requires the registry or a disposable local cache |
| Run controls | Device, dtype, batch size, decoding, and four seeds were recorded | One regression command now enforces the complete protocol |
| Task identity | Result files contained task hashes; sample files contained document, prompt, and target hashes | Committed SHA-256 manifests independently protect each evaluation input |
| Evidence | Aggregate results and per-sample logs were saved locally | A committed regression baseline defines minimums; the gate recomputes grades from fresh sample evidence |
| Version control | The project itself had no Git history, so results reported `git_hash: null` | The project is a Git repository, and clean-source checks give the recorded commit a precise meaning |
| Caches | `.cache/` was ignored and separate from source | Caches are documented as disposable speedups and model-response caching is excluded from evidence runs |
| Final test | A separate task existed and had not been run | Routine checks no longer load its cases or labels; a release-only command requires an explicit release identifier |

## Clean-source preflight

`lm_eval` records the current Git `HEAD`, but that hash does not describe
uncommitted modifications or untracked task files. A run from a dirty work tree
can therefore claim a commit whose contents differ from the files actually used.

The regression workflow begins with:

```bash
.venv/bin/python scripts/check_clean_tree.py
```

The check rejects modified, staged, and untracked source files. Ignored caches,
virtual environments, and generated results do not affect it. This gives the
`git_hash` in a subsequent result a precise meaning: the run used the tracked
contents of that commit.

## Evaluation-input manifests

Git identifies the complete source tree. The smaller evaluation manifests make
the behavioral inputs explicit and independently check them before a run:

- `pyproject.toml` and `uv.lock`
- the pinned Qwen run configuration
- the shared task template and selected task YAML
- the selected JSONL dataset
- the custom Python scorer
- the approved regression baseline or predeclared final decision policy

It also records dataset membership, the model repository and immutable revision,
chat-template setting, batch size, device, few-shot count, and all four seeds.

Verify the committed manifest:

```bash
.venv/bin/python scripts/eval_manifest.py
```

That default verifies only the routine regression inputs. Routine commands do
not read the separate final manifest; release maintainers verify it only while
preparing or executing the final gate:

```bash
.venv/bin/python scripts/eval_manifest.py --scope final_test
```

When an intentional reviewed change alters an evaluation input, regenerate it:

```bash
.venv/bin/python scripts/eval_manifest.py --write
# Release maintainers only:
.venv/bin/python scripts/eval_manifest.py --scope final_test --write
```

Regeneration is an explicit acceptance of a new evaluation identity. It must not
be used merely to silence an unexpected mismatch.

## Approved regression baseline

The source manifest answers, "Are we running the declared evaluation?" The
approved baseline answers, "Did its protected behavior regress?"

[`baselines/customer-support-regression-qwen2.5-0.5b-instruct.json`](../baselines/customer-support-regression-qwen2.5-0.5b-instruct.json)
records the accepted model revision, task hash, case count, package versions,
reference metrics, and minimum metrics. The gate permits improvements and rejects
scores below those minimums.

The result checker also requires the saved Git hash to identify the current
commit, finds the matching sample JSONL, recomputes every per-case grade through
the current scorer, and confirms that their means equal the saved aggregates.

Run the complete routine regression gate with:

```bash
./scripts/run_milestone_10_regression_gate.sh
```

It performs, in order:

1. Clean-source preflight.
2. Frozen dependency synchronization.
3. Evaluation-manifest verification.
4. Scorer and dataset-contract tests.
5. A fresh five-case Qwen regression run.
6. Baseline, provenance, sample-evidence, and metric verification.

The routine gate never selects `customer_support_tool_calls_final_test`.

Dependency and model downloads use project-local directories under `.cache/`.
They remain ignored and disposable: deleting `.cache/` can make the next run
slower or require registry access, but it does not alter the declared evaluation
identity or approved baseline.

## Clean-checkout verification

The strongest check starts without the working directory's virtual environment,
generated results, or uncommitted files:

```bash
./scripts/verify_clean_checkout.sh
```

The script clones the current local commit into a temporary directory, recreates
`.venv` from `uv.lock`, verifies the regression manifest, runs scorer and routine
dataset tests, and loads only the development and regression task definitions.
It deliberately does not load or evaluate the final holdout. It then deletes the
temporary clone. A shared download cache may make installation faster, but the
clone contains no generated evaluation artifacts and the verification does not
depend on earlier result files. On the same host, the script explicitly reuses
the installed Python 3.12 interpreter to bootstrap the new virtual environment;
dependencies are still installed afresh from the lockfile.

## Holdout integrity and the release-only gate

The three splits have different jobs:

| Split | When it is used | What happens afterward |
|---|---|---|
| Development | Repeatedly while building prompts, metrics, and integrations | Keep it available for diagnosis and iteration |
| Regression | On every relevant change | Add cases when a real failure is understood and fixed |
| Final test | Once choices are frozen for a predeclared release decision | Report the result; do not tune against it |

The routine regression and clean-checkout commands do not load the final dataset
or select the final task for inference. The final workflow has a separate
manifest, contract check, selected Qwen configuration, output directory, and
evidence checker. It refuses to start unless a release identifier is declared,
and each release identifier can be used only once:

```bash
FINAL_EVAL_RELEASE_ID=release-2026-09 \
  ./scripts/run_milestone_10_final_test.sh
```

The script reserves the identifier immediately before inference. A failed or
interrupted attempt still consumes it; the next attempt must use a new declared
identifier so evidence from separate attempts cannot be confused.

The committed
[`policies/customer-support-final-release.json`](../policies/customer-support-final-release.json)
sets the decision rule before the first run: all five metrics must meet their
minimums (100% valid JSON, 60% valid schema, 80% correct tool, 60% correct
arguments, and 60% exact call). These are tutorial thresholds chosen to require
the selected model to preserve its accepted regression-level behavior on the
balanced final set; they are not a production service-level objective.

That command is intentionally documented but has not been executed in this
course. When it is eventually run, it checks clean source, the frozen
environment, final-input hashes and dataset contract, performs fresh model
inference, saves aggregate and sample evidence under the release identifier,
recomputes every grade, and returns failure when any predeclared minimum is
missed.

The wrapper enforces the supported workflow, but it is a process control rather
than an access boundary. Because this teaching repository contains the data and
config, a team member could bypass the wrapper and run the task directly. Real
enforcement requires restricted holdout storage and a release CI identity.

## Contamination: two different risks

**Training contamination** means a model encountered evaluation cases, answers,
or close variants during pretraining or fine-tuning. A high score might then
measure recall instead of generalization. A task can declare a
`doc_to_decontamination_query`, but a query alone proves nothing: checking it
requires access to a relevant training corpus or index. We do not have Qwen's
complete training corpus, so this project does not claim a corpus-level proof of
decontamination. The locally authored cases and immutable older model revision
reduce the practical risk for this tutorial.

**Development contamination** means the team observes holdout cases or results
and then changes the model, prompt, parser, or scorer in response. Process
separation reduces that risk. This repository keeps the final JSONL in source
so the exercise is inspectable; therefore it is an untouched-by-tuning holdout,
not a blind access-controlled holdout. A production system should store final
cases in restricted storage and let release CI fetch them only at the declared
gate.

## Completion criterion

A clean local clone can recreate the locked environment, verify routine source
hashes, and load the development and regression tasks. The regression gate then
performs fresh inference and produces auditable results whose model revision,
task identity, configuration, seeds, dependency versions, source commit, sample
responses, and recomputed grades are known. The final test has a separate
declared workflow, single-use release identifier, and committed decision policy,
and it remains unrun.

Milestone 10 is complete when both routine commands pass:

```bash
./scripts/verify_clean_checkout.sh
./scripts/run_milestone_10_regression_gate.sh
```
