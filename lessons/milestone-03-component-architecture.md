# Milestone 3: Component architecture and file formats

## Goal

Understand how the harness components communicate and what representation crosses
each boundary. This milestone stays one level above the details of any particular
benchmark.

The central idea is that an evaluation run is a sequence of transformations:

```text
run settings
  -> task definition
  -> dataset rows
  -> rendered prompt and target
  -> request Instances
  -> raw model responses
  -> filtered responses
  -> per-example metrics
  -> aggregate results
  -> persisted result files
```

No single file contains the complete evaluation. Configuration files describe the
pieces, while Python objects carry the evaluation through memory at runtime.

## Two different YAML schemas

The harness uses YAML for two distinct purposes.

### Run-configuration YAML

A run configuration chooses what to execute and how to execute it:

```yaml
model: hf
model_args:
  pretrained: EleutherAI/pythia-14m
  dtype: float32
tasks:
  - course_piqa
include_path: custom_tasks
num_fewshot: 0
device: cpu
batch_size: 1
limit: 20
output_path: results/milestone-06/zero-shot
log_samples: true
```

It is the file equivalent of CLI flags. `EvaluatorConfig` loads it, and an explicit
CLI argument can override a value from it.

### Task-configuration YAML

A task configuration defines what one benchmark means:

```yaml
task: course_piqa
dataset_path: baber/piqa
dataset_kwargs:
  revision: 142f6d7367fd9877f0fb3b5734ea6a545f54cdd1
output_type: multiple_choice
training_split: train
validation_split: validation
doc_to_text: "Question: {{goal}}\nAnswer:"
doc_to_target: label
doc_to_choice: "{{[sol1, sol2]}}"
metric_list:
  - metric: acc
    aggregation: mean
    higher_is_better: true
  - metric: acc_norm
    aggregation: mean
    higher_is_better: true
```

It tells `ConfigurableTask` where examples come from, how dataset fields become
model input and reference answers, which model operation to request, and how to
grade and aggregate results.

Both files use YAML syntax, but they are consumed by different configuration
schemas:

| Question | Run YAML | Task YAML |
|---|---|---|
| Which model and adapter? | Yes | No |
| Which tasks should run? | Yes | No |
| Device, batch size, and output path? | Yes | No |
| Which dataset and split? | No | Yes |
| How does a row become a prompt and target? | No | Yes |
| Which metric grades the response? | No | Yes |

YAML stores data. It does not call the model or calculate the metrics by itself.
Python code validates the YAML and performs the declared behavior.

## The runtime representations

Consider this PIQA dataset row:

```python
{
    "goal": "How do I ready a guinea pig cage for it's new occupants?",
    "sol1": "Provide ... bedding made of ripped paper strips ...",
    "sol2": "Provide ... bedding made of ripped jeans material ...",
    "label": 0,
}
```

At runtime, the row passes through these representations.

### 1. Dataset source to row dictionary

`datasets.load_dataset("baber/piqa", revision="142f6d...")` obtains the source
data at the pinned revision and exposes named Hugging Face `Dataset` splits. The
selected split yields ordinary mapping-like rows to the task.

The source may be Parquet, JSON/JSONL, CSV, or a dataset loading script. The local
processed Hugging Face cache commonly uses Arrow. Those storage formats do not
change the task contract: template code receives one row by field name.

### 2. Row dictionary to rendered task fields

Jinja expressions in the task YAML read fields from the row:

```text
doc_to_text   -> "Question: How do I ready ...?\nAnswer:"
doc_to_choice -> ["Provide ... paper strips ...", "Provide ... jeans ..."]
doc_to_target -> 0
```

`doc_to_text` produces the model context. `doc_to_choice` produces candidate
continuations. For a multiple-choice task, `doc_to_target` produces the index of
the correct candidate.

Simple transformations can remain in Jinja. A task can reference a Python helper
with `!function` when the transformation is too awkward or complex for a template.

### 3. Rendered fields to `Instance` objects

`Task.build_all_requests()` coordinates iteration and few-shot context creation.
`ConfigurableTask.construct_requests()` turns the rendered example into the
operations supported by the model interface.

PIQA has two choices, so one dataset row creates two in-memory requests:

```python
Instance(
    request_type="loglikelihood",
    arguments=(prompt, " " + sol1),
)

Instance(
    request_type="loglikelihood",
    arguments=(prompt, " " + sol2),
)
```

`Instance` is a Python object. It is not a YAML or dataset file.

### 4. Instances to raw responses

The evaluator groups Instances by `request_type` and dispatches each group to the
corresponding model-adapter method. For this example:

```python
lm.loglikelihood([instance_for_sol1, instance_for_sol2])
```

The adapter returns one result per request:

```python
[(-160.18, False), (-165.18, False)]
```

The evaluator stores repeated raw returns on each Instance in `Instance.resps`.

### 5. Raw responses to filtered responses

A filter pipeline extracts, selects, or normalizes model responses before grading.
Its output is stored in `Instance.filtered_resps`. With one deterministic
likelihood response and the default filter, this mostly unwraps the one response.

Filters matter more for generated answers. For example, a regex filter could turn:

```text
"After checking the policy, the answer is REFUND."
```

into:

```text
"REFUND"
```

The raw response remains available for inspection.

### 6. Filtered responses to per-example metrics

The task's result-processing code compares the filtered response with the
reference. PIQA chooses the choice with the greatest likelihood and compares its
index with `label`.

For the example above:

```text
-160.18 > -165.18
predicted index = 0
reference index = 0
per-example acc = 1
```

A metric is evaluated per example before aggregation.

### 7. Per-example metrics to aggregate metrics

The configured aggregator combines the per-example values. With mean accuracy:

```text
aggregate accuracy = sum(per-example accuracy) / number of examples
```

The harness also estimates standard error. Aggregation therefore produces both a
headline value and information about its sampling uncertainty.

## Persisted output formats

With an output path and `log_samples: true`, the evaluation tracker writes two
main artifacts.

### Aggregate results: `results_*.json`

This is one complete JSON object containing run configuration, task versions,
sample counts, aggregate metrics, and standard errors. It answers questions about
the evaluation run as a whole.

### Sample log: `samples_<task>_*.jsonl`

JSONL means JSON Lines: every line is a separate valid JSON object. Each line can
hold one example's original document, request arguments, raw and filtered
responses, reference target, and metric values. It supports streaming large logs
one case at a time.

```text
results JSON   -> one object for the run
samples JSONL  -> one object per evaluated example
```

## Components and boundary objects

| From | To | Representation crossing the boundary |
|---|---|---|
| User | CLI/config loader | Shell arguments or run YAML |
| Task discovery | Task factory | Task YAML and registry/index entries |
| Dataset loader | Task | Hugging Face `Dataset` rows |
| Templates/mappings | Request builder | Prompt, target, and choice Python values |
| Request builder | Evaluator | `Instance` objects |
| Evaluator | Model adapter | Lists of Instances grouped by request type |
| Model adapter | Evaluator | Scores or generated strings |
| Filters | Task metric processing | Filtered response values |
| Task | Aggregator | Per-example metric values |
| Evaluation tracker | Filesystem | Aggregate JSON and sample JSONL |

## When YAML needs Python

A custom evaluation can remain YAML-only when existing components can:

- load its dataset;
- express its prompt, choices, and reference with field mappings or Jinja;
- use an existing request type;
- filter the response with registered filters; and
- grade it with an existing metric.

Add Python when the evaluation needs behavior such as a custom dataset transform,
domain-specific response parser, custom grading rule, or new model backend. The
task YAML can reference some helper functions with `!function`; the helper remains
Python even though its name appears in YAML.

## Checkpoint

Given a customer-support evaluation, classify each item by both component and
representation:

1. `model: hf`, `tasks: [support_actions]`, and `output_path: results/support`.
2. `doc_to_text: "Customer: {{message}}\nAction:"` and `metric: exact_match`.
3. `{"message": "The mug arrived broken", "expected_action": "REFUND"}`.
4. `Instance(request_type="generate_until", arguments=(prompt, gen_kwargs))`.
5. The string `"I would issue a REFUND."` returned by the adapter.
6. The string `"REFUND"` produced by a response filter.
7. The value `1` returned for that example.
8. Accuracy `0.87` across 100 examples.
9. The files that preserve the run-level result and the individual cases.

**Complete when:** Starting from a run command, you can draw the path to
`results_*.json`; state which steps are configuration, in-memory Python objects,
or persisted files; and explain when a custom evaluation needs Python in addition
to YAML.
