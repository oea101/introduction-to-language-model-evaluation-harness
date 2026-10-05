# Milestone 7: Reading results

## Goal

Separate what an aggregate score directly establishes from statistical
uncertainty, benchmark validity, and the causes of individual failures. Trace a
headline metric down to the exact document, request, model result, and grading
decision.

## Point estimate and effective sample

The controlled PIQA run reports:

```text
acc = 0.65
acc standard error = 0.1094
```

The results file also records:

```json
"n-samples": {
  "course_piqa": {
    "original": 1838,
    "effective": 20
  }
}
```

`original` is the size of the complete validation split. `effective` is the
number of documents actually scored after applying `limit: 20`. The observed
accuracy therefore means that 13 of those 20 documents received an `acc` grade
of one. It does not mean that the model answered 65% of all 1,838 documents
correctly.

## Standard error

For binary accuracy, the reported standard error is approximately:

```text
SE = sqrt(p * (1 - p) / (n - 1))
   = sqrt(0.65 * 0.35 / 19)
   = 0.1094
```

It estimates how much the measured mean could vary across different comparable
samples. It does not describe nondeterminism when rerunning the same model on the
same inputs.

A rough 95% interval is:

```text
0.65 +/- 1.96 * 0.1094 = approximately 0.44 to 0.86
```

More examples reduce sampling variance at roughly `1 / sqrt(n)`. They do not
repair selection bias, bad labels, data contamination, metric mismatch, or a
benchmark that does not represent the intended production workload.

Standard deviation and standard error answer different questions. Standard
deviation describes variation among individual outcomes. Standard error
describes uncertainty in the estimated average.

## Scope of the claim

A narrow interval on PIQA supports a precise claim about performance on the PIQA
protocol and similar physical-reasoning questions. It does not estimate
customer-support accuracy. A support claim requires an untouched test set that
covers the production support distribution, including its important and risky
categories.

## Aggregate metrics and slices

An aggregate is weighted by the number of examples in each slice. A dominant
easy category can hide a weak but important category:

| Slice | Cases | Accuracy | Correct |
|---|---:|---:|---:|
| Password resets | 80 | 95% | 76 |
| Refunds | 20 | 40% | 8 |
| Overall | 100 | 84% | 84 |

The overall 84% does not establish readiness for refunds. Useful support slices
may include intent, policy category, selected tool, risk, language, and number of
conversation turns.

## From aggregate to sample

Count failures and metric disagreements in the sample log:

```bash
sample_file=$(find results/milestone-06/zero-shot -name 'samples_course_piqa_*.jsonl' | sort | tail -1)

jq -s '{
  total: length,
  acc_failures: ([.[] | select(.acc == 0)] | length),
  acc_norm_failures: ([.[] | select(.acc_norm == 0)] | length),
  disagreements: ([.[] | select(.acc != .acc_norm)] | length)
}' "$sample_file"
```

The controlled run contains 20 samples, seven `acc` failures, seven `acc_norm`
failures, and four cases where the two metrics make different decisions. Equal
aggregate values therefore do not imply identical per-example behavior.

Inspect the first raw-accuracy failure:

```bash
jq -s '[.[] | select(.acc == 0)][0] |
  {doc_id, doc, arguments, filtered_resps, target, acc, acc_norm}' \
  "$sample_file"
```

One failure has the vague goal `dresser` and awkward answer choices. The model's
prediction disagrees with the reference, so it is an evaluation failure, but the
item quality weakens any claim that it reveals a physical-reasoning deficit.

A clearer failure asks what material a steel rocking chair is made from. The
model assigns a higher likelihood to the plastic-frame choice than the
steel-frame reference. This is stronger evidence of a capability failure.

## Failure diagnosis

An `acc` value of zero says that the evaluation protocol marked an example
wrong. Diagnose the cause before deciding how to respond:

| Observation | Candidate cause |
|---|---|
| Ambiguous question or choices | Dataset quality |
| Plausible answer with wrong reference | Label quality |
| Unexpected rendered input | Prompt or template construction |
| Clear prompt and reference, wrong model preference | Model capability |
| Correct raw output, wrong extracted value | Response filter |
| Correct filtered value, wrong grade | Metric implementation |

Ambiguous or mislabeled cases need independent adjudication. Clear model
failures can become development cases and, after a fix, regression cases.

**Complete when:** You can state the population and effective sample behind a
score, interpret its standard error without confusing it with run randomness,
identify relevant failure slices, and trace a failed aggregate point through the
sample record to its likely cause.
