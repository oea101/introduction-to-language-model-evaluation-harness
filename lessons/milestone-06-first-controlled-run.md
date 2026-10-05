# Milestone 6: First controlled run

## Goal

Run a small evaluation from an explicit configuration, preserve enough evidence
to audit it, and distinguish matching aggregate scores from a reproduction of the
same per-example behavior.

## Run configuration

The experiment is defined in
[`configs/piqa-pythia-14m.yaml`](../configs/piqa-pythia-14m.yaml). It records the
model adapter, immutable model revision, task, few-shot setting, dtype, device,
batch size, sample limit, four random seeds, and output settings.

```yaml
model: hf
model_args:
  pretrained: EleutherAI/pythia-14m
  revision: cf967c0a9a04383db6f7b1108d86b2962634b4ac
  dtype: float32

tasks:
  - course_piqa
include_path: custom_tasks
num_fewshot: 0

device: cpu
batch_size: 1
limit: 20
seed:
  - 0
  - 1234
  - 1234
  - 1234

output_path: results/milestone-06/zero-shot
log_samples: true
write_out: true
```

The seeds apply to Python, NumPy, PyTorch, and few-shot sampling in that order.
The project pins `lm_eval` and its Python dependencies in `uv.lock`.

Run the evaluation from the project root:

```bash
./scripts/run_milestone_06_controlled.sh
```

For an already-populated Hugging Face cache, force an offline run with:

```bash
HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 ./scripts/run_milestone_06_controlled.sh
```

The script accepts an optional device override:

```bash
./scripts/run_milestone_06_controlled.sh mps
```

Configuration precedence is:

```text
harness defaults -> YAML configuration -> explicit CLI overrides
```

`--show_config` prints the final merged configuration. The results JSON also
stores the effective configuration, which is the auditable record of what the
run actually used.

## What the run produced

The controlled run evaluated 20 of PIQA's 1,838 validation documents. Each
document has two choices, so the harness executed 40 likelihood requests. The
result was:

| Metric | Value | Standard error |
|---|---:|---:|
| `acc` | 0.65 | 0.1094 |
| `acc_norm` | 0.65 | 0.1094 |

The 0.65 accuracy means 13 of the 20 evaluated documents received a grade of
one. It is not a measurement over all 1,838 documents, and the first 20 documents
need not represent the full split.

## Output artifacts

One run with one task and `log_samples: true` creates two logical artifacts:

```text
results_<timestamp>.json
samples_course_piqa_<timestamp>.jsonl
```

The aggregate results JSON covers the whole run. It contains task-level metrics,
sample counts, task configurations and versions, the effective model/run
configuration, seeds, package versions, and environment information.

The sample JSONL contains one record per evaluated document. Important fields
include:

| Field | Meaning |
|---|---|
| `doc` / `doc_hash` | Source dataset document and its fingerprint |
| `arguments` / `prompt_hash` | Constructed requests and a fingerprint of the shared prompt context |
| `target` / `target_hash` | Reference answer and its fingerprint |
| `resps` | Raw adapter results; no built-in response hash is recorded |
| `filtered_resps` | Results after the configured response filter |
| `acc`, `acc_norm` | Per-document metric values |

For multiple tasks, one aggregate results file contains entries for every task,
while each task receives its own sample JSONL file.

`write_out: true` prints a few prompt/request examples to the terminal for
inspection. It does not create the sample JSONL; `log_samples: true` does that and
therefore requires `output_path`.

## Reproduction strength

Two runs can have the same aggregate accuracy while answering different cases
correctly. Compare progressively stronger evidence:

1. Aggregate metrics match.
2. Dataset documents, prompts, targets, and per-example grades match.
3. Complete request arguments, raw responses, filtered responses, and grades
   match.

The original and reproduced runs matched at the third level for all 20 examples.
Their files are not byte-identical because timestamps and other incidental run
metadata differ.

When runs diverge, the first differing field helps locate the responsible stage:

| First difference | Likely stage |
|---|---|
| `doc_hash` | Dataset contents, selection, or preprocessing |
| `prompt_hash` | Prompt construction, few-shot context, or chat formatting |
| `resps` | Model or inference configuration |
| Same raw response, different `filtered_resps` | Response filtering |
| Same filtered response, different metric | Grading logic |

**Complete when:** You can execute the configured run, explain why it creates 40
model requests but 20 sample records, account for both output artifact types, and
verify reproduction below the aggregate-score level.
