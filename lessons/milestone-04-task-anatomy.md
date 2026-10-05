# Milestone 4: Task anatomy

## Goal

Start with one untouched dataset row and predict every model request produced by
the task definition.

## The PIQA contract

The runnable course task is defined in
`custom_tasks/course_piqa/course_piqa.yaml`. It mirrors the built-in task at
`upstream/lm-evaluation-harness/lm_eval/tasks/piqa/piqa.yaml` and adds an
immutable dataset revision:

```yaml
task: course_piqa
dataset_path: baber/piqa
dataset_name: null
dataset_kwargs:
  revision: 142f6d7367fd9877f0fb3b5734ea6a545f54cdd1
output_type: multiple_choice
training_split: train
validation_split: validation
test_split: null
doc_to_text: "Question: {{goal}}\nAnswer:"
doc_to_target: label
doc_to_choice: "{{[sol1, sol2]}}"
should_decontaminate: true
doc_to_decontamination_query: goal
metric_list:
  - metric: acc
    aggregation: mean
    higher_is_better: true
  - metric: acc_norm
    aggregation: mean
    higher_is_better: true
metadata:
  version: 1.0
```

Because no test split is configured, `eval_docs` uses the validation split. The
training split is available for few-shot examples; `lm_eval` does not train the
model.

## Render one row

Consider this dataset row:

```python
{
    "goal": "How do I ready a guinea pig cage for it's new occupants?",
    "sol1": "Provide the guinea pig with a cage full of a few inches of bedding made of ripped paper strips, you will also need to supply it with a water bottle and a food dish.",
    "sol2": "Provide the guinea pig with a cage full of a few inches of bedding made of ripped jeans material, you will also need to supply it with a water bottle and a food dish.",
    "label": 0,
}
```

The three mappings return:

```text
doc_to_text(row)
  -> "Question: How do I ready a guinea pig cage for it's new occupants?\nAnswer:"

doc_to_choice(row)
  -> [row["sol1"], row["sol2"]]

doc_to_target(row)
  -> 0
```

`doc_to_target` does not enter the model prompt. It is retained as the answer key
for grading.

## Construct the requests

`target_delimiter` is not present in PIQA's YAML, so `TaskConfig` supplies its
default value: one space.

`ConfigurableTask.construct_requests()` combines the context with each choice and
creates two Instances:

```python
Instance(
    request_type="loglikelihood",
    idx=0,
    arguments=(
        "Question: How do I ready a guinea pig cage for it's new occupants?\nAnswer:",
        " Provide the guinea pig with a cage full of a few inches of bedding made of ripped paper strips, you will also need to supply it with a water bottle and a food dish.",
    ),
)

Instance(
    request_type="loglikelihood",
    idx=1,
    arguments=(
        "Question: How do I ready a guinea pig cage for it's new occupants?\nAnswer:",
        " Provide the guinea pig with a cage full of a few inches of bedding made of ripped jeans material, you will also need to supply it with a water bottle and a food dish.",
    ),
)
```

The YAML says `multiple_choice`, but the model-interface request type is
`loglikelihood`. `multiple_choice` is task behavior that expands one document into
one likelihood request per choice.

## Verify your derivation

At this point in the course you have not run the model yet. Compare your
derivation with the Milestone 4 section of the answer key. After Milestone 6,
the generated `samples_course_piqa_*.jsonl` file provides a second, runtime
check: `arguments.gen_args_0` and `arguments.gen_args_1` should correspond to
the two Instances above, and the target should be serialized as `"0"`.

## Independent exercise

Use this second row:

```python
{
    "goal": "dresser",
    "sol1": "replace drawer with bobby pin ",
    "sol2": "finish, woodgrain with  bobby pin ",
    "label": 1,
}
```

Before reading its saved sample, derive:

1. The exact string returned by `doc_to_text`.
2. The ordered list returned by `doc_to_choice`.
3. The value returned by `doc_to_target` and what that index means.
4. The `request_type`, `idx`, context, and continuation of every Instance.
5. Which values are sent to the model and which value is retained only for grading.

After completing Milestone 6, verify against the runtime evidence with:

```bash
sample_file=$(find results/milestone-06/zero-shot -name 'samples_course_piqa_*.jsonl' -print -quit)
sed -n '2p' "$sample_file" | jq '{doc, arguments, target}'
```

**Complete when:** Given a new PIQA row, you can derive the rendered prompt, ordered
choices, answer key, number of Instances, request types, and exact argument tuples
without inspecting the sample log.
