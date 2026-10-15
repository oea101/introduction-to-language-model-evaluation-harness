# Introduction to EleutherAI Language Model Evaluation Harness 

A hands-on, conversational course for **AI Product Managers** who want to
understand what happens beneath a model evaluation score.

The course uses
[EleutherAI's Language Model Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness),
usually called `lm_eval`. According to the project's README, the harness powers
the [Hugging Face Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard),
has been used in
[hundreds of papers](https://scholar.google.com/scholar?authuser=2&cites=15052937328817631261%2C4097184744846514103%2C1520777361382155671%2C17476825572045927382%2C18443729326628441434%2C14801318227356878622%2C7890865700763267262%2C12854182577605049984%2C15641002901115500560%2C5104500764547628290&hl=en&oi=bibs),
and is used inside organizations including NVIDIA, Cohere, BigScience, BigCode,
Nous Research, and Mosaic ML.

This repository packages a real walkthrough rather than a new application. You
inspect the harness, predict its behavior, run small evaluations, read the
evidence, compare controlled experiments, and turn a customer-support product
requirement into a custom evaluation.

## Who this is for

This course is written strictly for AI Product Managers, especially those
working with model development, model selection, evaluation platforms, or
quality and release decisions. It assumes comfort with product concepts and a
willingness to read small pieces of YAML, JSON, and Python. It does not assume
that you build production software.

The practical benefit is better evaluation judgment. You will be able to spot
when a leaderboard number does not support a product claim, define diagnostic
metrics for a product behavior, compare models without confounding the test, and
ask for the evidence needed before a launch or regression decision.

## What you will learn

By the end, you should be able to:

- explain what a dataset, task, model adapter, request, filter, metric, and
  aggregation each contribute to an evaluation;
- distinguish likelihood scoring from generated-answer scoring;
- read a task YAML and predict the requests it creates;
- interpret accuracy, normalized accuracy, exact match, standard error, and
  per-sample evidence;
- design a controlled model or prompt comparison;
- translate a product behavior into layered evaluation metrics;
- separate development, regression, and final-test data;
- ask whether a reported score is reproducible and broad enough for the product
  decision being made.

## The 10 milestones

| Milestone | Product question | Hands-on outcome |
|---|---|---|
| [1. Harness mental model](lessons/milestone-01-harness-mental-model.md) | What problem does a harness solve? | Map every part of an evaluation lifecycle. |
| [2. Source orientation](lessons/milestone-02-source-orientation.md) | Where does each responsibility live? | Trace `lm-eval run` from CLI to saved evidence. |
| [3. Components and formats](lessons/milestone-03-component-architecture.md) | How do the pieces communicate? | Separate run YAML, task YAML, runtime objects, JSON, and JSONL. |
| [4. Task anatomy](lessons/milestone-04-task-anatomy.md) | How does a benchmark become executable? | Render a PIQA row into exact model requests. |
| [5. Requests and scoring](lessons/milestone-05-model-requests-and-scoring.md) | What does the model calculate? | Derive predictions from likelihoods and generated text. |
| [6. First controlled run](lessons/milestone-06-first-controlled-run.md) | Can we execute and preserve the pipeline? | Run a pinned 20-case evaluation and save its evidence. |
| [7. Reading results](lessons/milestone-07-reading-results.md) | What does the score establish? | Trace an aggregate to individual failures and uncertainty. |
| [8. Controlled experiments](lessons/milestone-08-controlled-experiments.md) | Is the comparison fair? | Change one factor at a time and compare paired outcomes. |
| [9. Custom evaluation](lessons/milestone-09-custom-evaluation.md) | How does a product requirement become an eval? | Grade structured customer-support tool calls with five metrics. |
| [10. Reproducible workflow](lessons/milestone-10-reproducible-evaluation.md) | Can another person audit and repeat it? | Check provenance, manifests, regression gates, and holdout rules. |

Read the [curriculum map](lessons/00-lm-eval-roadmap.md) for the full sequence
or the [course recap](lessons/lm-eval-course-recap.md) after completing it.

## Quick start with Codex

Prerequisites:

- macOS, Linux, or Windows through WSL;
- Git, [`uv`](https://docs.astral.sh/uv/), `jq`, and
  [`ripgrep`](https://github.com/BurntSushi/ripgrep);
- internet access for the first setup and model downloads;
- roughly 5 GB of free disk space for the environment, caches, and small models.

No model API key is required. The exercises run open-weight models locally on
CPU by default; download and inference time varies by computer.

```bash
git clone https://github.com/oea101/introduction-to-language-model-evaluation-harness.git
cd introduction-to-language-model-evaluation-harness
./scripts/setup_course.sh
```

Open the cloned folder as a project in
[Codex](https://developers.openai.com/learn/codex) and send:

> Start Introduction to the Language Model Evaluation Harness. Teach me
> interactively, one question at a time.

Codex will use [`AGENTS.md`](AGENTS.md),
[`CODEX_INSTRUCTOR.md`](CODEX_INSTRUCTOR.md), and the facilitator
[answer key](answer-key/README.md) to recreate the guided conversation. Your
local progress is saved in the ignored `course-progress.md` file.

Follow [START_HERE.md](START_HERE.md) for setup troubleshooting, resuming a
lesson, or taking the course without Codex.

## What the exercises run

The course pins `lm_eval` 0.4.13, exact model revisions, and an exact PIQA
dataset revision. The first benchmark uses Pythia-14M so that likelihood scoring
can run on an ordinary CPU. Later milestones compare Pythia-70M and use
Qwen2.5-0.5B-Instruct for a small, locally authored customer-support task.

The customer-support exercise grades text that represents a tool call. It tests
tool selection, JSON structure, and argument extraction. It does not execute a
tool, change an environment, or evaluate multi-step recovery.

The included datasets are intentionally tiny and teach evaluation mechanics;
their scores do not establish production readiness. The committed final-test
split illustrates release process controls but is visible to repository readers,
so it is not a blind holdout. The course leaves it unrun.

## Repository map

```text
.
├── START_HERE.md             learner setup and launch instructions
├── CODEX_INSTRUCTOR.md       interactive teaching contract
├── COURSE_PROGRESS_TEMPLATE.md
├── answer-key/               facilitator prompts, answers, and misconceptions
├── lessons/                  the 10 milestone chapters and recap
├── configs/                  complete, pinned evaluation run settings
├── custom_tasks/             pinned PIQA mirror and customer-support task
├── scripts/                  setup, runs, comparisons, and reproducibility checks
├── tests/                    tests for the custom scorer and data contracts
├── examples/                 evidence samples that can be read before inference
├── baselines/                accepted regression thresholds
├── manifests/                hashes of release-relevant evaluation inputs
└── policies/                 predeclared final-test decision rule
```

## Reproducibility boundary

The repository pins the course protocol, but hardware and low-level numerical
libraries can still produce small likelihood differences. The lesson teaches
learners to compare configuration, documents, prompts, targets, responses, and
per-case grades instead of treating one matching aggregate as proof of an
identical run.

## Contributing and attribution

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a lesson or evaluation
change. Third-party projects, datasets, and model cards are listed in
[ATTRIBUTIONS.md](ATTRIBUTIONS.md). Course-authored source and documentation are
released under the [MIT License](LICENSE).
