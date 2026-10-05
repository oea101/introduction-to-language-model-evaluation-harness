# Course PIQA task

`course_piqa.yaml` mirrors the built-in PIQA task in
`lm-evaluation-harness` v0.4.13 and gives the Hugging Face dataset an immutable
revision. The course can therefore teach from the official task while keeping
its runnable experiments reproducible.

The functional task fields match
`lm_eval/tasks/piqa/piqa.yaml` at tag `v0.4.13`, commit
`ddd67220430a2470529f25fd5c05a576ca1057a0`. The course adds:

```yaml
dataset_kwargs:
  revision: 142f6d7367fd9877f0fb3b5734ea6a545f54cdd1
```

The external task name is `course_piqa`, which prevents it from shadowing the
built-in `piqa` task. This repository does not redistribute the PIQA dataset;
the harness downloads it from the configured Hugging Face source when you run
the evaluation. See `ATTRIBUTIONS.md` for source and license information.
