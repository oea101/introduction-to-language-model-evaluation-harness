# Milestone 1: Harness mental model

## The central idea

An evaluation harness is the execution engine for a repeatable experiment. It brings a system under test, evaluation cases, an execution procedure, grading rules, and aggregation together in one run.

```text
system under test + cases + procedure + grading + run settings
                              |
                              v
                     evaluation harness
                              |
                              v
              responses + per-case grades + summary
```

A benchmark supplies the capability and cases to test. The harness performs the test. The two are related, but they are not the same thing.

## The components

| Component | Plain-language meaning | What it does not contain |
|---|---|---|
| Model | The system whose behavior we want to measure | The definition of success |
| Model adapter | A translator between the harness interface and a particular inference backend | The benchmark questions |
| Dataset | Raw examples, usually divided into named splits | Instructions for turning rows into model requests |
| Evaluation case | One input situation plus enough reference information to grade it | The aggregate result |
| Task | The executable evaluation specification connecting dataset rows to prompts, requests, references, and metrics | Model weights |
| Prompt/template | The rule that converts fields from a dataset row into the text or messages shown to the model | The model response |
| Request | One operation the task asks the model adapter to perform | The final grade |
| Response | What the model adapter returns for a request | Whether the response is acceptable |
| Filter | Optional extraction or cleanup applied before grading | The dataset's reference answer |
| Metric or scorer | The rule that compares one processed response with the reference and produces a grade | The summary across all cases |
| Aggregation | The rule that combines per-case grades into a dataset-level result | The individual prompt or response |
| Harness | The software that coordinates loading, execution, grading, aggregation, logging, and caching | A claim that a particular benchmark is valid for your product |
| Run configuration | The chosen model, tasks, seeds, batch size, prompting options, limits, and output settings | The implementation of those components |
| Evaluation run | One concrete execution of a model, task, and run configuration | A timeless property of the model |
| Benchmark | A named measurement protocol: one or more tasks, their data, prompting rules, and metrics | The general-purpose execution engine |

An evaluation case and a model request are not necessarily one-to-one. A generation case may create one request. A multiple-choice case with four candidates may create four likelihood requests, then convert the four responses into one predicted choice and one per-case grade.

## One example from beginning to end

Imagine evaluating a customer-support assistant on damaged-order requests.

### 1. Dataset row

```json
{
  "customer_message": "Two mugs arrived broken. Replace them, but keep the rest.",
  "order_items": [
    {"sku": "mug", "quantity": 2},
    {"sku": "plate", "quantity": 4}
  ],
  "expected_action": {
    "type": "replace",
    "sku": "mug",
    "quantity": 2
  }
}
```

This is data. By itself, it does not specify what the model sees or how the response is graded.

### 2. Task and template

The task could render the row into:

```text
You are a customer-support assistant.

Order:
- 2 mugs
- 4 plates

Customer: Two mugs arrived broken. Replace them, but keep the rest.

Return the proposed action as JSON.
```

The task also chooses the request type, identifies `expected_action` as the reference, and selects a metric.

### 3. Request and model adapter

The task creates a generation request. The model adapter translates that standard request into the input expected by a local Hugging Face model, vLLM server, or remote model API.

### 4. Response and filter

Suppose the model returns:

```text
Certainly. {"type":"replace","sku":"mug","quantity":2}
```

A filter might extract the JSON object and parse it into structured data.

### 5. Metric

The metric compares the parsed action with `expected_action`. It might award:

```text
1 = exact action, item, and quantity
0 = anything else
```

This example earns `1`.

### 6. Aggregation

If 92 of 100 cases earn `1`, mean accuracy is:

```text
(92 × 1 + 8 × 0) / 100 = 0.92
```

The harness also records uncertainty and preserves enough run information to investigate the eight failures.

## The full lifecycle

```text
1. Read the run configuration.
2. Resolve the requested model adapter and task.
3. Load the task's dataset split.
4. Convert each row into prompts, references, and model requests.
5. Execute requests through the model adapter.
6. Filter or parse the responses when required.
7. Apply a metric to every case.
8. Aggregate the per-case values.
9. Save run metadata, summary metrics, and optional sample logs.
```

## Four distinctions to keep clear

### Dataset versus task

A dataset contains rows. A task explains how those rows become an evaluation. The same dataset can support different tasks, prompts, request types, and metrics.

### Benchmark versus harness

A benchmark defines what is measured. A harness executes that definition consistently across models and environments.

### Reference versus metric

A reference describes the expected result. A metric defines how much credit a response receives relative to that reference. One reference can be graded by exact match, partial credit, semantic similarity, a model judge, or an environment-state check.

### Model score versus model property

A score belongs to the complete run:

```text
model + model version + adapter + task version + dataset split
+ prompt/template + few-shot examples + metric + run settings
```

Changing any of those can change the result. Saying only that “the model scored 92%” omits the conditions under which the score was produced.

## Checkpoint

Using the customer-support example, identify the component represented by each item:

1. A file containing 100 customer messages and expected actions
2. A function that converts one row into instructions for the assistant
3. A wrapper that sends a standard generation request to a Hugging Face model
4. A rule that returns `1` only when action type, SKU, and quantity all match
5. The mean of the 100 per-case grades
6. A multiple-choice dataset contains 5 cases with 4 choices each: how many likelihood requests, per-case accuracy values, and aggregate accuracy values are produced?

**Complete when:** You can name the first five components, answer the counting question, and explain why the dataset alone is not an executable evaluation.
