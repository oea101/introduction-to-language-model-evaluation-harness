# Milestone 9: Custom evaluation

## Goal

Turn a product requirement into an external `lm_eval` task that can be
discovered, loaded, run, and scored without editing the installed harness. This
task measures whether a customer-support model selects a tool and constructs its
arguments as one JSON object. It grades text that represents a tool call; it does
not execute the tool.

## Product contract

The input is a customer message. The required output has exactly two top-level
keys:

```json
{"name":"<tool name>","arguments":{}}
```

The available tools are `track_order`, `cancel_order`, `create_replacement`,
`issue_refund`, and `escalate_to_human`. Their argument names, types, and allowed
enum values are defined in
[`custom_tasks/customer_support_tool_calls/utils.py`](../custom_tasks/customer_support_tool_calls/utils.py).

## Components

| Component | File | Responsibility |
|---|---|---|
| Shared task template | [`_customer_support_tool_calls_template_yaml`](../custom_tasks/customer_support_tool_calls/_customer_support_tool_calls_template_yaml) | Prompt, generation request, scorer, metrics, and aggregation |
| Split task YAML | [`customer_support_tool_calls_dev.yaml`](../custom_tasks/customer_support_tool_calls/customer_support_tool_calls_dev.yaml) and its peers | Task name, dataset path, and split metadata |
| Dataset | [`data/`](../custom_tasks/customer_support_tool_calls/data) | Messages and canonical expected calls |
| Custom scorer | [`utils.py`](../custom_tasks/customer_support_tool_calls/utils.py) | Parses each response and returns five per-case scores |
| Run configuration | [`configs/`](../configs) | Model, immutable revision, chat formatting, device, seeds, and output path |
| Harness evaluator | pinned `lm_eval` dependency | Builds requests, calls the model adapter, collects per-case scores, and averages them |

The three task YAML files use `include:` to inherit one extensionless template.
Only their task names and dataset paths differ, preventing prompt or metric drift
between splits.

YAML can wire the dataset, prompt, generation request, and existing metrics. The
five diagnostics need Python because they parse JSON, validate tool-specific
argument types and enum values, and compare nested objects. That is the boundary
for adding `utils.py` instead of forcing behavior into a template.

## Dataset lifecycle

| Split | Cases | Use |
|---|---:|---|
| Development | 10 | Inspect and edit while developing the prompt, schema, and scorer |
| Regression | 5 | Preserve known failures and run after every behavioral change |
| Final test | 10 | Estimate final performance at a predeclared evaluation gate |

The tutorial regression rows represent simulated production incidents and record
their provenance and failure mode. In a real product, each row should point to
the real incident or bug that justified adding it. The final-test configuration
exists, but the final set was not run during this lesson.

## Grading

`process_results(doc, results)` parses the first generated response and emits
five independent binary values:

| Metric | Question |
|---|---|
| `valid_json` | Can `json.loads` parse the complete response? |
| `valid_tool_schema` | Is it an object with exactly `name` and `arguments`, a known tool, and the required argument names, types, and enum values? |
| `correct_tool` | Does `name` equal the reference tool? |
| `correct_arguments` | Does the arguments object equal the reference arguments object? |
| `exact_tool_call` | Is the schema valid and the complete parsed object equal to the reference? |

These metrics are diagnostic rather than a strict hierarchy. A response can use
the correct tool while omitting its arguments, or extract the correct arguments
while selecting the wrong tool. The final metric is:

```python
exact_tool_call = valid_tool_schema and actual == expected
```

Each YAML metric uses `aggregation: mean`, so a score is the fraction of cases
whose per-case value is `1`.

## Model-swap experiment

The regression set was first run with `EleutherAI/pythia-70m`, a base completion
model selected for fast CPU exercises. It produced no exact tool calls. The
comparison model is
[`Qwen/Qwen2.5-0.5B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct),
pinned to revision `7ae557604adf67be50417f59c2c2f167def9a775`. Its model card
specifically describes improvements in instruction following and structured JSON
generation.

Three conditions separate the model change from prompt serialization:

| Condition | Changed from previous condition |
|---|---|
| Pythia-70M, plain prompt | Baseline |
| Qwen2.5-0.5B-Instruct, plain prompt | Model package: weights, architecture, tokenizer, pretraining, and instruction tuning |
| Qwen2.5-0.5B-Instruct, chat template | Model-specific chat serialization only |

All conditions use the same five regression documents, references, task prompt,
scorer, zero-shot setting, greedy decoding, 128-token limit, float32 dtype, CPU,
batch size, and random seeds. The chat-template condition wraps the same task
prompt as one user message and adds Qwen's assistant-generation prefix.

### Aggregate results

| Condition | Same serialized prompt as baseline | `valid_json` | `valid_tool_schema` | `correct_tool` | `correct_arguments` | `exact_tool_call` |
|---|:---:|---:|---:|---:|---:|---:|
| Pythia-70M, plain prompt | Yes | 20% | 0% | 0% | 0% | 0% |
| Qwen2.5-0.5B-Instruct, plain prompt | Yes | 20% | 20% | 20% | 20% | 20% |
| Qwen2.5-0.5B-Instruct, chat template | No | 100% | 60% | 80% | 60% | 60% |

Changing only the model produced one exact call instead of zero. Using the
instruction model with its intended chat format produced three exact calls and
valid JSON on every case. The full 60-point difference between the first and
third rows belongs to the practical model-plus-format configuration; it should
not be attributed to model weights alone.

The model-package comparison does not identify whether parameter count,
architecture, tokenizer, pretraining, or instruction tuning caused the gain.
Even when the serialized prompt strings match, different tokenizers can map them
to different token sequences.

### Paired exact-match outcomes

| Regression case | Pythia plain | Qwen plain | Qwen chat |
|---|:---:|:---:|:---:|
| `reg_track_001` | Fail | Fail | Fail |
| `reg_cancel_001` | Fail | Fail | Pass |
| `reg_replace_001` | Fail | Fail | Pass |
| `reg_refund_001` | Fail | Pass | Fail |
| `reg_escalate_001` | Fail | Fail | Pass |

The chat-formatted Qwen run still failed two cases:

- Tracking: it returned `{"name":"track_order"}` without the required
  `arguments` object. Tool selection was correct, but schema and arguments were
  wrong.
- Refund: it selected `cancel_order` and supplied an unsupported `sku` argument.
  The JSON syntax was valid, but tool selection, schema, and arguments were
  wrong.

With only five cases, each decision moves an aggregate by 20 percentage points.
The `exact_tool_call` standard error at 60% is approximately 24.5 percentage
points. A reported standard error of zero at 0/5 does not mean there is no
uncertainty. This run demonstrates the harness and exposes concrete behavior; it
does not establish a stable population-level or production accuracy estimate.

## Run and compare

Run all three regression conditions and print the aggregate and paired tables:

```bash
./scripts/run_milestone_09_model_comparison.sh
```

Print a comparison from the latest saved runs without invoking a model:

```bash
.venv/bin/python scripts/compare_milestone_09_models.py
```

The model configurations are:

- [`customer-support-tool-calls-regression-pythia-70m.yaml`](../configs/customer-support-tool-calls-regression-pythia-70m.yaml)
- [`customer-support-tool-calls-regression-qwen2.5-0.5b-instruct-raw-prompt.yaml`](../configs/customer-support-tool-calls-regression-qwen2.5-0.5b-instruct-raw-prompt.yaml)
- [`customer-support-tool-calls-regression-qwen2.5-0.5b-instruct.yaml`](../configs/customer-support-tool-calls-regression-qwen2.5-0.5b-instruct.yaml)

The unit and dataset-contract checks are:

```bash
.venv/bin/python -m unittest -v tests/test_customer_support_tool_calls.py
```

**Complete when:** The external task is discoverable and loadable; its reference
calls all pass the scorer; development, regression, and final-test cases have
distinct roles; saved sample logs explain every aggregate; and a model change can
be compared without silently changing the evaluated cases or grading rules.
