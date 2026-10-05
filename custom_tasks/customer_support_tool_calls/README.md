# Customer-support tool-call task

This external `lm_eval` task treats a tool call as generated JSON text. It does
not execute the tool.

Each row contains a customer message and a canonical expected call. The task asks
the model to emit exactly one JSON object and reports five metrics:

| Metric | Meaning |
|---|---|
| `valid_json` | The complete response can be parsed by `json.loads` |
| `valid_tool_schema` | The tool exists and its exact argument names, types, and enum values are valid |
| `correct_tool` | The generated tool name matches the reference |
| `correct_arguments` | The generated arguments object exactly matches the reference |
| `exact_tool_call` | The entire call is schema-valid and exactly matches the reference |

The three task YAML files inherit the same prompt, generation settings, scorer,
and metrics from `_customer_support_tool_calls_template_yaml`. Only the task name
and data file differ.

| Split | File | Use |
|---|---|---|
| Development | `data/development.jsonl` | Inspect and iterate while building the task |
| Regression | `data/regression.jsonl` | Run on every change to protect known fixes |
| Final test | `data/final_test.jsonl` | Run only at the predeclared final evaluation gate |

The tutorial regression rows use explicit `simulated_production_incident`
provenance. A production project should record the real incident or bug that
caused every regression case to be added.

Discover the routine development and regression tasks:

```bash
.venv/bin/lm-eval ls tasks --include_path custom_tasks \
  | grep -E 'customer_support_tool_calls_(dev|regression)$'
```

Validate the routine definitions without running a model:

```bash
for task in \
  customer_support_tool_calls_dev \
  customer_support_tool_calls_regression
do
  .venv/bin/lm-eval validate --tasks "$task" --include_path custom_tasks
done
```

Run the development or regression configuration:

```bash
.venv/bin/lm-eval run \
  --config configs/customer-support-tool-calls-dev-pythia-70m.yaml

.venv/bin/lm-eval run \
  --config configs/customer-support-tool-calls-regression-pythia-70m.yaml
```

The selected final-test configuration is
`configs/customer-support-tool-calls-final-test-qwen2.5-0.5b-instruct.yaml`.
Milestone 10's routine scripts omit it from validation and prompt development.
The supported release-only runner is documented in
[`lessons/milestone-10-reproducible-evaluation.md`](../../lessons/milestone-10-reproducible-evaluation.md).

The reproducible Pythia-versus-Qwen regression comparison is documented in
[`lessons/milestone-09-custom-evaluation.md`](../../lessons/milestone-09-custom-evaluation.md).
Run it with:

```bash
./scripts/run_milestone_09_model_comparison.sh
```

The tasks remain outside the installed `lm_eval` package. `--include_path`
provides plugin-style discovery.
