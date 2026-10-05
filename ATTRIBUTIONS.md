# Attributions

This course combines original teaching material and synthetic customer-support
examples with third-party open-source software, a public benchmark dataset, and
open model weights. Each external asset remains governed by its own terms.

## Language Model Evaluation Harness

- Project: [EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness)
- Course version: `v0.4.13`, commit
  `ddd67220430a2470529f25fd5c05a576ca1057a0`
- License: [MIT](https://github.com/EleutherAI/lm-evaluation-harness/blob/v0.4.13/LICENSE.md)

The `course_piqa` YAML mirrors the functional fields of the project's PIQA task
at that version and adds a fixed dataset revision. The upstream source is cloned
during local setup and is not copied into this repository.

## PIQA

- Dataset: Physical Interaction: Question Answering (PIQA)
- Authors: Yonatan Bisk, Rowan Zellers, Ronan Le Bras, Jianfeng Gao, and Yejin Choi
- Paper: [PIQA: Reasoning about Physical Commonsense in Natural Language](https://doi.org/10.1609/aaai.v34i05.6239)
- Original data page: [PIQA repository](https://github.com/ybisk/ybisk.github.io/tree/master/piqa)
- Original data license: [Academic Free License 3.0](https://opensource.org/license/afl-3-0-php)
- Harness source mirror used at runtime: [`baber/piqa`](https://huggingface.co/datasets/baber/piqa), revision
  `142f6d7367fd9877f0fb3b5734ea6a545f54cdd1`

This repository does not include the PIQA dataset. The setup and run commands
download it into an ignored local cache. Short rows shown in the lesson are used
only to explain task transformation and evaluation behavior.

## Pythia

- Model cards: [Pythia-14M](https://huggingface.co/EleutherAI/pythia-14m) and
  [Pythia-70M](https://huggingface.co/EleutherAI/pythia-70m)
- Project: [EleutherAI/pythia](https://github.com/EleutherAI/pythia)
- License shown by the model cards: Apache License 2.0

The course downloads exact model revisions declared in `configs/`; it does not
redistribute model weights.

## Qwen2.5

- Model card: [Qwen/Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- License shown by the model card: Apache License 2.0
- Course revision: `7ae557604adf67be50417f59c2c2f167def9a775`

The course downloads the pinned model revision into an ignored local cache and
does not redistribute model weights.

## Hugging Face Open LLM Leaderboard

The README's description of adoption follows the official harness README. The
current leaderboard is available at the
[Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard).

This independent course is not affiliated with or endorsed by EleutherAI,
Hugging Face, the PIQA authors, EleutherAI's Pythia project, or the Qwen team.
