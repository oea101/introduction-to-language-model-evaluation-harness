# Facilitator answer key

This guide preserves the sample questions, expected answers, hints, and common
misconceptions from the original interactive walkthrough. Learners should
attempt each question before consulting it. Codex should use it as assessment
guidance rather than recite it.

## Milestone 1: Harness mental model

**Opening prompt:** Match each artifact to a harness concept.

| Artifact | Expected concept |
|---|---|
| A file with 100 customer messages and expected actions | Dataset |
| A function that converts one row into assistant instructions | Task transformation, usually part of the task |
| A wrapper that sends standard requests to a Hugging Face model | Model adapter |
| A rule that returns `1` only when action, SKU, and quantity match | Per-case metric |
| The mean of 100 per-case grades | Aggregation |

**Follow-up:** A multiple-choice dataset has five cases and four choices per
case. How many likelihood requests, per-case accuracy values, and aggregate
accuracy values are produced?

**Answer:** 20 likelihood requests, five predictions and per-case grades, and
one aggregate accuracy for that task and metric. One case expands into one
request per choice; the scores collapse into one predicted index, then one
grade.

**Hint:** Count model operations, cases, and reported means separately.

**Common misconception:** “Four choices means four accuracy values per case.”
Accuracy grades the selected choice against the single reference after all four
candidates have been scored.

## Milestone 2: Source orientation

**Opening prompt:** In `lm_eval/__main__.py`, describe what `cli_evaluate()` does.

**Expected answer:** It sets up logging, constructs the `HarnessCLI`, parses the
arguments into a namespace, and dispatches execution. Accept plain-language
descriptions.

**Next prompt:** Name the three top-level CLI command families in v0.4.13.

**Answer:** `run`, `ls`, and `validate`.

**Trace prompt:** Which object does the run command build before it reaches
`simple_evaluate()`?

**Answer:** `EvaluatorConfig`. `simple_evaluate()` then calls the core
`evaluate()` path after resolving the model and tasks.

**Source checkpoint answers:**

1. Shell entry point: `pyproject.toml`.
2. `hf` adapter alias: `lm_eval/models/huggingface.py`, class `HFLM`.
3. Official PIQA declaration: `lm_eval/tasks/piqa/piqa.yaml`.
4. Orchestration: `lm_eval/evaluator.py`.
5. Persistence: `lm_eval/loggers/evaluation_tracker.py`.
6. Adapter contract: `lm_eval/api/model.py`.

**Question learners often ask:** What are groups?

**Answer:** A group is a named collection of tasks or subtasks with rules for
reporting them together. A task defines one evaluation contract; a group lets a
single name select and summarize several contracts.

## Milestone 3: Components and file formats

**Prompt:** Identify these five objects: the file selecting model/device/tasks;
the file mapping dataset fields; one source example; one concrete model
operation; and the validated Python object holding task settings.

**Answer:** Run configuration, task configuration, dataset row, `Instance`, and
`TaskConfig` respectively.

**Prompt:** Where are supported task YAML attributes defined?

**Answer:** Start with `lm_eval/config/task.py` for `TaskConfig`, then follow task
behavior in `lm_eval/api/task.py`. Run-level fields live in
`lm_eval/config/evaluate_config.py`.

**Prompt:** Does `doc_to_text` save the prompt or the answer?

**Answer:** It renders the context presented to the model. `doc_to_target`
provides the reference used for grading; `doc_to_choice` provides the ordered
candidate continuations for multiple choice.

**Prompt:** What do `{{goal}}`, `{{sol1}}`, and `{{sol2}}` mean?

**Answer:** They are Jinja expressions that read fields from the current dataset
row. The question can be produced by `doc_to_text` while `doc_to_choice` reads
the answer fields separately; all mappings receive the same row.

**Common misconception:** “YAML performs inference.” YAML declares the wiring.
Python validates it, creates runtime objects, invokes the adapter, and computes
metrics.

## Milestone 4: Task anatomy

Use the exercise row in `lessons/milestone-04-task-anatomy.md`.

**Expected derivation:**

- `doc_to_text` returns `Question: dresser\nAnswer:`.
- `doc_to_choice` returns the ordered two-element list containing `sol1`, then
  `sol2`, including their original whitespace.
- `doc_to_target` returns integer `1`, meaning the second choice is the key.
- The task creates two `loglikelihood` Instances with indexes `0` and `1`.
- Both use the same rendered context. Each continuation is one leading delimiter
  space plus the corresponding choice.
- Context and continuations go to the model. Label `1` remains with the task for
  grading and is not shown as an answer key in the prompt.

**Follow-up:** How many Instances are produced and why?

**Answer:** Two, because `multiple_choice` creates one likelihood request for
each candidate.

**Common misconception:** “The question must appear inside `doc_to_choice`.”
`doc_to_text` and `doc_to_choice` are combined by task construction after each
has read the same source row.

## Milestone 5: Model requests and scoring

**Interface prompt:** What do the three adapter methods return or measure?

- `loglikelihood(requests)` scores a known continuation conditioned on a context
  and returns its summed log probability plus whether the continuation was
  greedy.
- `loglikelihood_rolling(requests)` scores complete text across rolling windows,
  commonly for perplexity-style evaluation.
- `generate_until(requests)` produces continuation text under generation and
  stop settings.

The task transforms rows into these standard requests in
`ConfigurableTask.construct_requests()`; the model adapter translates the
standard requests into backend-specific tensor or API operations.

**Numeric prompt:** Candidate likelihoods are `[-10, -7]`, and the reference
index is `1`. What are the prediction and accuracy?

**Answer:** Predicted index `1`; per-case `acc = 1`. `-7` is the higher model
score, not the accuracy.

**Normalized prompt:** Choices are `short` and `a much longer answer`, with
likelihoods `-4` and `-10`; reference index is `1`.

**Answer:** Raw likelihood picks index `0`, so `acc = 0`. Character-normalized
scores are `-4/5 = -0.8` and `-10/20 = -0.5`; normalized scoring picks index
`1`, so `acc_norm = 1`.

**Masking explanation:** A causal model receives context plus a known candidate
for scoring. The shifted labels and causal attention mask ensure the position
predicting a continuation token sees only earlier tokens. One forward pass can
compute the conditional probability of every known continuation token in
parallel. Supplying the candidate does not reveal future tokens to the position
that predicts them.

**When to choose generation:** Use a generative task when production behavior is
the text the model emits, such as an option letter, JSON object, or assistant
answer. Use candidate likelihood when the evaluation intends to compare how a
base language model scores fixed continuations.

## Milestone 6: First controlled run

**Config prompt:** Divide the run configuration into four groups.

**Answer:**

1. Adapter and model identity: `model: hf` and pinned `model_args`.
2. Evaluation contract: `course_piqa`, include path, and `num_fewshot: 0`.
3. Runtime controls: CPU, float32, batch size, limit, and four seeds.
4. Evidence controls: output path, `log_samples`, and `write_out`.

**Artifact prompt:** What disappears if `write_out` is removed? What disappears
if `log_samples` is removed? What if `output_path` is removed?

**Answer:** `write_out` removes the small prompt preview from terminal output.
`log_samples` removes the per-case JSONL evidence. Without `output_path`, there
is no persistent result destination; `log_samples` requires one.

**Count prompt:** Why do 20 cases create 40 requests but only 20 sample rows?

**Answer:** Each PIQA case has two candidate continuations, so it makes two
likelihood requests. Those two scores produce one prediction and one sample
record for the source case.

**Hash prompt:** Is `response_hash` a hash of the raw model response?

**Answer:** This harness sample schema does not include a response hash. It
stores raw `resps`. `doc_hash`, `prompt_hash`, and `target_hash` fingerprint the
source row, rendered context, and reference target. They change across different
cases because those contents change; the same case under the same protocol
should reproduce them.

## Milestone 7: Reading results

**Prompt:** What does `acc = 0.65`, standard error `0.1094`, and effective sample
size `20` establish?

**Answer:** Thirteen of the 20 evaluated cases received grade one. The standard
error estimates sampling uncertainty in that mean under the evaluation sample;
it is not model rerun randomness. It does not establish 65% performance over the
full PIQA split or a customer-support workload.

**Prompt:** If a larger model differs from 0.65 by less than this uncertainty,
can we claim an improvement?

**Answer:** No strong improvement claim follows from this small sample. Use
paired case transitions and an interval for the difference, then expand the
sample if the decision requires greater precision.

**Failure prompt:** Which slice deserves attention when the overall score hides
weak behavior in refunds?

**Answer:** The refund slice, alongside other material product-risk slices. A
weighted aggregate can hide a small, costly category.

**Diagnosis rule:** A grade of zero is the beginning of investigation. Check
source quality, reference quality, rendered prompt, raw response, filtered
response, and metric logic before labeling it a capability failure.

## Milestone 8: Controlled experiments

**Few-shot prompt:** What are the five shots?

**Answer:** Five solved training examples inserted into each evaluation prompt
as demonstrations. They are context, not additional scored cases and not
training updates to the model weights.

**Seed prompt:** What does a fixed few-shot seed control?

**Answer:** It makes pseudorandom demonstration selection and ordering
repeatable. Changing it can select different demonstrations; it does not change
the 20 evaluation cases.

**Experiment prompt:** Why run several predeclared few-shot seeds?

**Answer:** To measure sensitivity to demonstration selection, not to search for
and report only the best seed. Report the distribution and paired case changes.

**Control prompt:** When comparing Pythia-14M and Pythia-70M, what should change?

**Answer:** Model repository and revision. Keep task, cases, prompt, target,
few-shot setting, dtype, device, batch size, seeds, and metrics fixed. Record
resource use as part of the product tradeoff.

## Milestone 9: Custom evaluation

**Metric prompt:** Name five useful grades for a textual tool call.

**Answer:** `valid_json`, `valid_tool_schema`, `correct_tool`,
`correct_arguments`, and `exact_tool_call`.

Use these worked cases:

| Output condition | valid JSON | valid schema | correct tool | correct args | exact call |
|---|---:|---:|---:|---:|---:|
| Not JSON | 0 | 0 | 0 | 0 | 0 |
| Valid JSON, unknown tool, correct-looking arguments | 1 | 0 | 0 | 0 | 0 |
| Permitted tool and exact arguments | 1 | 1 | 1 | 1 | 1 |
| Correct tool and arguments plus an extra top-level key | 1 | 0 | 1 | 1 | 0 |

For a valid call with the right tool but wrong quantity, the useful diagnosis is
`1, 1, 1, 0, 0`.

**Lifecycle prompt:** A previously unseen production failure is understood and
fixed. Which set should permanently protect it?

**Answer:** Regression. Development remains the freely inspected workspace;
final test remains reserved for the frozen decision.

**Why scores were low:** Pythia base models were not instruction-tuned to follow
the JSON contract. The Qwen instruction model improved structured output, while
sample-level comparison still showed which schema and argument failures
remained. A model swap is interpretable only when the task cases and scoring
contract stay fixed.

**Boundary:** This evaluates tool selection and argument construction expressed
as text. It does not execute the tool or observe subsequent state, tool replies,
multi-step planning, or recovery.

## Milestone 10: Reproducible evaluation workflow

**Identity prompt:** What must be pinned or recorded for a reproducible run?

**Answer:** Source commit, locked dependencies, exact model and dataset
revisions, task/prompt/scorer/data contents, runtime settings, chat template,
few-shot configuration, seeds, and the evidence files.

**Prompt:** Why do both a manifest and sample log matter?

**Answer:** The manifest fingerprints declared inputs; the sample log explains
behavior by preserving documents, requests, outputs, and grades. A hash detects
change but does not diagnose a model response.

**Prompt:** Why check for a clean Git tree?

**Answer:** A result's Git hash names only committed content. Uncommitted or
untracked evaluation files could otherwise produce evidence that falsely appears
to come from that commit.

**Prompt:** What does a clean clone add?

**Answer:** It tests whether setup, task discovery, tests, and manifests work
without hidden local files, an old environment, or generated outputs.

**Holdout prompt:** Should the final test contain copies of development and
regression cases?

**Answer:** No. Those familiar cases would make the final estimate partly
measure material already used for iteration. Keep final cases distinct and
representative of the broader workload. After a development or production
failure is fixed, add it to regression when its behavior should remain
protected.

**Course limitation:** The final data is committed and therefore visible. The
release script is a teaching process control, not an access boundary. A real
blind holdout belongs in restricted storage and is fetched by a release identity.

**Final synthesis question:** A team reports “Model B scored 4 points higher.”
What do you ask before supporting the launch?

**Strong answer:** Ask what product behavior and decision the score represents;
whether cases and high-risk slices match production; whether the same protocol
and cases were used; how responses were filtered and graded; the effective
sample, uncertainty, and paired failures; the cost and latency tradeoff; and
whether another person can recreate the exact evaluation identity.
