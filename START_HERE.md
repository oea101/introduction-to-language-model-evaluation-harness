# Start here

This course is a guided walkthrough of `lm_eval` for AI Product Managers. You
will inspect real source and configuration, answer short questions, make
predictions, and then run small local evaluations. You are not building an app.

## 1. Clone and set up the course

Install Git, `uv`, `jq`, and `ripgrep`, then run:

```bash
git clone https://github.com/oea101/introduction-to-language-model-evaluation-harness.git
cd introduction-to-language-model-evaluation-harness
./scripts/setup_course.sh
```

The setup script:

1. creates a locked Python 3.12 environment under `.venv`;
2. clones the upstream harness at tag `v0.4.13` and verifies its exact commit;
3. creates your ignored `course-progress.md` file;
4. runs the scorer tests and task-definition preflight.

The first model run downloads open model weights and the pinned PIQA dataset.
Those downloads live under the ignored `.cache/` directory.

## 2. Start the interactive lesson in Codex

Open this repository folder as the project in Codex. Start a task and send:

> Start Introduction to the Language Model Evaluation Harness. Teach me
> interactively, one question at a time.

Codex should first check your setup, explain how the course works, and begin
Milestone 1 with a single question. It should wait for your response before
giving feedback or asking the next question.

If you stop, return to the same repository and send:

> Resume the Language Model Evaluation Harness course from my saved progress.

The tutor records completed checkpoints and your current question in
`course-progress.md`. That file is ignored by Git and remains local to you.

## 3. Useful learner prompts

You can steer the tutor naturally:

- `Explain that another way with a concrete example.`
- `Show me the exact file and line that defines this.`
- `Let me try before you reveal the answer.`
- `Slow down and ask one smaller question.`
- `Open the result file and walk through each field.`
- `Summarize what I learned in this milestone.`

Ask direct questions whenever a concept is unclear. The tutor should answer the
question, reconnect it to the current milestone, and continue from your saved
place.

## 4. Take the course without Codex

Copy the progress template and follow the curriculum in order:

```bash
cp COURSE_PROGRESS_TEMPLATE.md course-progress.md
```

Start with [`lessons/00-lm-eval-roadmap.md`](lessons/00-lm-eval-roadmap.md).
Each lesson contains a goal, explanation, checkpoint, and completion criterion.
Use [`answer-key/README.md`](answer-key/README.md) only after attempting a
checkpoint.

## Setup checks

Rerun the fast preflight at any time:

```bash
./scripts/preflight_course.sh
```

It does not run a model and does not run the final test.

If the preflight says a command is missing, install that prerequisite and run
`./scripts/setup_course.sh` again. If the upstream checkout is at a different
commit, remove only `upstream/lm-evaluation-harness` and rerun setup. Generated
environments, caches, and results can be removed and recreated from source.

The course runners default to Hugging Face's documented non-Xet HTTP download
path because anonymous Xet downloads can fail on some networks. To opt back into
Xet explicitly, prefix a run with `HF_HUB_DISABLE_XET=0`.

## Compute expectations

The smallest run evaluates 20 PIQA cases with a 14M-parameter model on CPU. The
customer-support comparison later downloads a 0.5B-parameter instruction model.
Plan for several short sessions. First runs take longer because dependencies,
datasets, and model weights must download; exact timing depends on your machine.
