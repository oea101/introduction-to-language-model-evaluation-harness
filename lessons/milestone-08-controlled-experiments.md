# Milestone 8: Controlled experiments

## Goal

Determine whether an observed evaluation difference can be attributed to one
intended change. Hold the evaluation cases, targets, task, metrics, seeds, and
runtime choices fixed unless one of them is the variable under study. Compare
paired sample outcomes and resource use in addition to aggregate scores.

## Experiment 1: zero-shot versus five-shot

The baseline and treatment configurations are:

- [`configs/piqa-pythia-14m.yaml`](../configs/piqa-pythia-14m.yaml)
- [`configs/piqa-pythia-14m-5shot.yaml`](../configs/piqa-pythia-14m-5shot.yaml)

Their behavioral difference is:

```diff
-num_fewshot: 0
+num_fewshot: 5
```

Their output paths also differ so their artifacts remain separate. The model,
immutable revision, dtype, task, 20 evaluation cases, metrics, batch size, device,
and seeds are identical.

Five-shot prompting inserts five solved training examples before each validation
question. These demonstrations are context rather than additional scored cases.
The run still creates 20 sample records and 40 likelihood requests: two candidate
continuations for each evaluation document.

Run the treatment with:

```bash
./scripts/run_milestone_08_five_shot.sh
```

The observed results were:

| Condition | `acc` | `acc_norm` |
|---|---:|---:|
| Zero-shot | 0.65 | 0.65 |
| Five-shot, seed 1234 | 0.60 | 0.65 |

For raw accuracy, one zero-shot success became a five-shot failure and no failure
was corrected. The paired mean difference was `-0.05`, with a paired standard
error of approximately `0.05` and a rough 95% interval from `-0.15` to `+0.05`.
This small experiment does not establish a general five-shot regression.

For normalized accuracy, one failure was corrected and one success regressed, so
the aggregate change was zero. This is another example of equal aggregate scores
hiding different decisions.

The request count stayed fixed, but the demonstrations made every context longer:

| Measurement | Zero-shot | Five-shot |
|---|---:|---:|
| Likelihood requests | 40 | 40 |
| Mean context tokens | 13.3 | 184.7 |
| Approximate tokens across requests | 1,272 | 8,124 |

The five-shot condition processed approximately 6.4 times as many tokens.

## Experiment 2: demonstration-selection sensitivity

`num_fewshot` controls the number of demonstrations. The fourth run seed controls
which training examples are selected and their ordering. A fixed seed is an
explicit, recorded pseudorandom seed; it does not mean that every validation
document necessarily receives the same five examples.

Run a specified five-shot seed with:

```bash
./scripts/run_milestone_08_fewshot_seed.sh 42
```

Four predeclared seeds produced:

| Few-shot seed | `acc` | `acc_norm` |
|---:|---:|---:|
| 7 | 0.65 | 0.65 |
| 42 | 0.65 | 0.60 |
| 1234 | 0.60 | 0.65 |
| 2026 | 0.65 | 0.65 |
| Mean | 0.6375 | 0.6375 |

Raw accuracy varied on one evaluation document. Normalized accuracy varied on
three documents. This demonstrates sensitivity to the selected demonstrations.
Reporting only the best seed would be seed cherry-picking. A robustness study
should predeclare its seeds and report the complete distribution. Repeating
few-shot seeds does not repair a small or unrepresentative evaluation dataset.

## Experiment 3: model comparison

The Pythia-70M treatment is defined in:

- [`configs/piqa-pythia-70m.yaml`](../configs/piqa-pythia-70m.yaml)
- [`scripts/run_milestone_08_pythia_70m.sh`](../scripts/run_milestone_08_pythia_70m.sh)

Both models used zero-shot prompting, the same 20 documents, prompt arguments,
targets, task version, dtype, device, batch size, seeds, and metrics. Only the
model repository and immutable revision changed.

| Measurement | Pythia-14M | Pythia-70M |
|---|---:|---:|
| Parameters | 14.1M | 70.4M |
| `acc` | 0.65 | 0.65 |
| `acc_norm` | 0.65 | 0.65 |
| Warm wall time | 7.15 s | 7.75 s |
| Likelihood throughput | approximately 334/s | approximately 127/s |

Raw accuracy decisions were identical for all 20 documents. Normalized accuracy
corrected one case and regressed another. On this CPU and tiny workload, the 70M
model processed likelihood requests about 2.6 times more slowly. The wall-time
difference was smaller because startup and dataset loading dominated. Reliable
latency claims require repeated runs and a representative workload.

The supported conclusion is limited to the experiment:

> On these 20 PIQA cases under this zero-shot protocol, Pythia-70M showed no
> aggregate improvement over Pythia-14M.

It does not establish that the models perform equally across PIQA or other tasks.

## Experimental discipline

Before running a comparison, identify:

1. The baseline and treatment.
2. The single intended behavioral variable.
3. The evaluation documents and primary metric.
4. Every control that must remain fixed.
5. Relevant slices and paired per-case transitions.
6. Statistical uncertainty and repeated seeds when applicable.
7. Token, latency, memory, and monetary costs.
8. The decision rule and scope of the resulting claim.

Changing the model and prompting method together creates a confounded comparison.
A two-by-two design is needed to separate model and prompting effects. Chat
templates are another possible controlled variable for chat or instruction
models, but they are not part of these Pythia base-model experiments.

**Complete when:** You can show that the compared runs used identical evaluation
inputs and controls, identify the intended configuration difference, analyze
paired behavior and uncertainty, account for resource tradeoffs, and state a
conclusion no broader than the evidence supports.
