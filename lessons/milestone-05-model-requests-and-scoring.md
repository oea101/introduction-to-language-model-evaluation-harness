# Milestone 5: Model requests and scoring

## Goal

Understand which operation the model performs and keep three different values
separate: the model's score or generated text, the task's prediction, and the
metric's grade.

## Model-interface operations

| Method | Arguments on each `Instance` | Adapter result |
|---|---|---|
| `loglikelihood` | `(context, continuation)` | `(summed_log_probability, is_greedy)` |
| `loglikelihood_rolling` | `(text,)` | Total log probability for the complete text |
| `generate_until` | `(context, generation_kwargs)` | Generated continuation string |

A task with `output_type: multiple_choice` creates one `loglikelihood` Instance
per choice. `multiple_choice` is task behavior rather than a fourth model-adapter
method.

## Three stages that must remain distinct

For two multiple-choice candidates:

```text
model scores       = [-10, -7]
predicted index    = argmax(scores) = 1
reference index    = 1
per-example acc    = int(predicted == reference) = 1
```

Both candidates are scored. Only one index is predicted. The accuracy grade is
binary and cannot be a negative likelihood value.

## Total versus length-normalized choice scores

`acc` selects the choice with the largest total log likelihood:

```text
prediction = argmax(choice_loglikelihoods)
```

`acc_norm` first divides every choice log likelihood by a length measure, then
selects a choice. In PIQA under harness v0.4.13, the denominator is the number of
characters in the raw choice string:

```text
normalized_score[i] = loglikelihood[i] / len(choice[i])
prediction_norm = argmax(normalized_scores)
```

The name `acc_norm` does not mean that the final accuracy is normalized. Candidate
scores are normalized before prediction; the resulting per-example metric is still
either zero or one.

### Real disagreement from the controlled run

```text
Question: how do you put eyelashes on?

choice 0: "glue them on with mascara."
choice 1: "put eyelash glue on the fake eyelashes ... let it dry on."
gold index: 1
```

| Choice | Total log likelihood | Characters | Normalized score |
|---|---:|---:|---:|
| 0 | -35.0908 | 26 | -1.3496 |
| 1 | -134.9920 | 131 | -1.0305 |

Raw scoring selects index 0, so `acc = 0`. Normalized scoring selects index 1, so
`acc_norm = 1`. Total likelihood tends to penalize longer continuations because it
adds more non-positive token log probabilities.

## Exact match

`exact_match` usually compares a filtered generated string with the reference
string. For a generative multiple-choice task:

```text
raw generation:       "B\nThe correct calculation is..."
filter output:        "B"
reference target:     "B"
per-example exact_match: 1
```

Exact-match options can permit transformations such as ignoring case or
punctuation. Filters and metric options are part of the evaluation definition and
must be preserved when comparing results.

The conceptual difference is:

```text
acc / acc_norm:
candidate likelihoods -> choose an index -> compare with reference index

exact_match:
generated text -> filter -> compare with reference text
```

## Low-level likelihood calculation

For a causal model, the adapter tokenizes a context and continuation, shifts the
sequence by one token, obtains vocabulary logits, applies log-softmax, gathers the
log probability assigned to every actual continuation token, and sums them:

```text
log P(y1 ... yn | context)
  = log P(y1 | context)
  + log P(y2 | context, y1)
  + ...
  + log P(yn | context, y1 ... y[n-1])
```

Causal attention prevents the position predicting a token from seeing that token
or later tokens. Because the continuation is known during scoring, the restricted
positions can be computed in parallel in one forward pass. Generation must append
unknown output tokens one at a time.

## Checkpoint

Given:

```text
choice texts: ["short", "a much longer answer"]
log likelihoods: [-4, -10]
reference index: 1
```

1. Which index does raw likelihood select, and what is `acc`?
2. Calculate each character-normalized score, select the normalized index, and
   determine `acc_norm`.
3. Why is neither `-4` nor `-10` an accuracy value?
4. For a generative task with target `"B"`, raw response `"B\nBecause..."`, and a
   first-line filter, what filtered value and `exact_match` grade result?

**Complete when:** You can explain why multiple-choice creates one logical request
per choice, derive a prediction from raw and normalized model scores, and grade a
filtered generated response with exact match.
