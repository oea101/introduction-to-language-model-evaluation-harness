# Milestone 9 comparison snapshot

Five synthetic regression cases were held fixed while the model and prompt
handling changed.

| Condition | Valid JSON | Valid schema | Correct tool | Correct arguments | Exact call |
|---|---:|---:|---:|---:|---:|
| Pythia-70M, plain prompt | 20% | 0% | 0% | 0% | 0% |
| Qwen2.5-0.5B-Instruct, plain prompt | 20% | 20% | 20% | 20% | 20% |
| Qwen2.5-0.5B-Instruct, chat template | 100% | 60% | 80% | 60% | 60% |

This snapshot shows why one exact score is insufficient. The intermediate
metrics reveal whether the change improved parseability, schema compliance,
tool choice, or argument extraction. Five cases are enough to teach the
mechanism and far too few to support a production launch claim.
