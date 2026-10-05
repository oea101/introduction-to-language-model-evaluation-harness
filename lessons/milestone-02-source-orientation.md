# Milestone 2: Source-code orientation

## Goal

Learn where the major harness components live and trace `lm-eval run` from the shell command to the evaluation engine. This milestone maps responsibilities to source files; it does not require understanding every implementation detail.

## The source checkout

The official source is cloned at:

```text
upstream/lm-evaluation-harness
```

It is pinned to release `v0.4.13`, commit `ddd67220430a2470529f25fd5c05a576ca1057a0`, matching the package installed in this project's virtual environment.

The checkout is a learning reference and is ignored by the outer project's `.gitignore`. Evaluation commands currently use the installed package under `.venv`, so browsing or annotating the reference checkout does not silently change our evaluation behavior.

This milestone traces the official built-in task named `piqa`. The runnable
course configurations use an external mirror named `course_piqa`. Its task
behavior is identical, but it pins the dataset revision so later experiments do
not silently change when the dataset repository changes.

Verify the checkout:

```bash
cd upstream/lm-evaluation-harness
git describe --tags --exact-match
git rev-parse HEAD
```

## First map of the repository

```text
lm-evaluation-harness/
├── pyproject.toml             package metadata and shell entry points
├── lm_eval/
│   ├── __main__.py            starts the CLI
│   ├── _cli/                  run, list, and validate commands
│   ├── config/                run, task, and group configuration schemas
│   ├── tasks/                 built-in task definitions and discovery
│   ├── api/                   core interfaces and shared abstractions
│   ├── models/                inference-backend adapters
│   ├── evaluator.py           central evaluation orchestration
│   ├── evaluator_utils.py     result processing and aggregation helpers
│   ├── filters/               response extraction and transformation
│   ├── loggers/               result and sample persistence
│   ├── caching/               reusable model-response caching
│   └── result_schema.py       shape of the returned aggregate result
├── docs/                      user, task, model, and Python API guides
└── tests/                     behavior and integration checks
```

## Component-to-source map

| Component | Start here | Responsibility |
|---|---|---|
| Package and executable | `pyproject.toml` | Declares version `0.4.13` and maps both `lm-eval` and `lm_eval` commands to `lm_eval.__main__:cli_evaluate` |
| CLI entry point | `lm_eval/__main__.py` | Configures logging, creates `HarnessCLI`, parses arguments, and dispatches the selected command |
| CLI command router | `lm_eval/_cli/harness.py` | Registers `run`, `ls`, and `validate` subcommands |
| Run command | `lm_eval/_cli/run.py` | Converts CLI input into an `EvaluatorConfig`, creates logging/tracking objects, and calls `simple_evaluate()` |
| Run configuration | `lm_eval/config/evaluate_config.py` | Merges defaults, an optional run YAML file, and CLI overrides; validates the final run settings |
| Task discovery | `lm_eval/tasks/manager.py` and `lm_eval/tasks/_index.py` | Scans built-in and included paths and resolves task, group, and tag names |
| Task construction | `lm_eval/tasks/_factory.py` and `lm_eval/tasks/_yaml_loader.py` | Loads YAML definitions and constructs task/group objects |
| Task configuration schema | `lm_eval/config/task.py` | Defines the supported task YAML fields |
| Task behavior | `lm_eval/api/task.py` | Implements `Task` and `ConfigurableTask`, renders documents, builds requests, applies filters, and converts responses into metrics |
| Request object | `lm_eval/api/instance.py` | Represents one model operation and stores its arguments, responses, filtered responses, and metadata |
| Model interface | `lm_eval/api/model.py` | Defines the standard operations every backend adapter must provide |
| Component aliases | `lm_eval/api/registry.py` | Registers and resolves model, metric, filter, and aggregation names |
| Hugging Face adapter | `lm_eval/models/huggingface.py` | Registers the aliases `hf`, `hf-auto`, and `huggingface` and implements them with Transformers/PyTorch |
| Other model adapters | `lm_eval/models/` | Implements vLLM, SGLang, local/API, multimodal, and other inference backends |
| Evaluation engine | `lm_eval/evaluator.py` | Instantiates models and tasks, builds all requests, groups them by type, executes them, applies filters, and produces per-case metrics |
| Aggregation helpers | `lm_eval/evaluator_utils.py` | Combines task metrics, computes standard errors, and processes task groups |
| Filters | `lm_eval/filters/` | Extracts, selects, or transforms model responses before scoring |
| Built-in metric utilities | `lm_eval/api/metrics.py` | Implements common metrics, aggregations, and statistical helpers |
| Result schema | `lm_eval/result_schema.py` | Documents the structured result returned by the evaluator |
| Persistence | `lm_eval/loggers/evaluation_tracker.py` | Writes aggregate results and optional per-sample logs locally or to supported trackers |
| Caching | `lm_eval/caching/cache.py` | Wraps a model with persistent response caching |
| Documentation | `docs/` | Explains CLI, task creation, model adapters, configuration files, and the Python API |
| Tests | `tests/` | Demonstrates expected behavior and protects the contracts above |

## Trace one command through the code

Start with:

```bash
lm-eval run --model hf --tasks piqa
```

Follow it through these files:

```text
1. pyproject.toml
   `lm-eval` resolves to `lm_eval.__main__:cli_evaluate`.

2. lm_eval/__main__.py
   `cli_evaluate()` creates the command-line parser and dispatches the command.

3. lm_eval/_cli/harness.py
   `HarnessCLI` recognizes `run` and delegates to the Run subcommand.

4. lm_eval/_cli/run.py
   `Run._execute()` builds and validates `EvaluatorConfig`, prepares the
   evaluation tracker, resolves the task manager, and calls `simple_evaluate()`.

5. lm_eval/evaluator.py: simple_evaluate()
   The string `hf` is resolved to a model-adapter class. The string `piqa` is
   resolved to a task definition. Seeds and model/task configuration are set.

6. lm_eval/evaluator.py: evaluate()
   Dataset rows become task requests. Requests are grouped by operation type
   and sent through the model adapter. Responses are attached to Instances,
   filtered, scored per example, and aggregated.

7. lm_eval/loggers/evaluation_tracker.py
   Aggregate JSON and optional per-sample JSONL artifacts are saved.
```

The shortest useful summary is:

```text
shell command
  -> CLI/config
  -> task and model resolution
  -> request construction
  -> adapter execution
  -> filtering and scoring
  -> aggregation and persisted results
```

## Three registries that should not be conflated

1. **Task index:** finds task, group, and tag definitions by scanning task YAML files.
2. **Component registries:** map aliases such as `hf`, metric names, and filter names to registered Python implementations.
3. **Hugging Face Hub:** an external model and dataset store. It supplies assets but is not an internal `lm_eval` registry.

## Guided source commands

Run these from `upstream/lm-evaluation-harness`:

```bash
# Find the shell entry point.
rg -n 'lm-eval.*cli_evaluate' pyproject.toml

# Find the function called by the shell entry point.
rg -n 'def cli_evaluate' lm_eval/__main__.py

# Find where the run command calls the evaluator.
rg -n 'simple_evaluate' lm_eval/_cli/run.py

# Find the Hugging Face adapter and its registered aliases.
rg -n 'register_model.*hf|class HFLM' lm_eval/models/huggingface.py

# Find the PIQA task definition.
find lm_eval/tasks/piqa -maxdepth 1 -type f -print

# Find the three core request operations on the model interface.
rg -n 'def loglikelihood|def loglikelihood_rolling|def generate_until' \
  lm_eval/api/model.py
```

## Checkpoint

Starting with this command:

```bash
lm-eval run --model hf --tasks piqa --output_path results
```

Answer these from the source map:

1. Which file makes `lm-eval` a valid shell command?
2. Which file resolves the alias `hf` to the Hugging Face adapter?
3. Which file contains PIQA's declarative task definition?
4. Which file coordinates request construction, model execution, and scoring?
5. Which file writes the result artifacts?
6. If you want to understand the contract every model adapter must satisfy, which file should you open?

**Complete when:** You can follow the command through the source tree and answer all six questions without treating the task YAML, model adapter, and evaluator as one component.
