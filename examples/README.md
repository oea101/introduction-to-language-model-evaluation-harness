# Curated evidence examples

This directory gives learners a small result shape to inspect before they run
local model inference. These files are course-authored summaries, not complete
`lm_eval` outputs and not a replacement for generated evidence.

- `milestone-06-controlled-run-summary.json` records the headline counts and
  metrics from the original 20-case Pythia-14M walkthrough.
- `milestone-09-model-comparison.md` records the small customer-support
  comparison used to motivate model swapping and layered metrics.

The course does not commit full PIQA sample logs or dataset records. Milestone 6
creates real `results_*.json` and `samples_course_piqa_*.jsonl` files under the
ignored `results/` directory on the learner's computer.
