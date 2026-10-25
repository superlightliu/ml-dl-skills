# ML & DL Learning Skills

A Chinese-first collection of 11 Agent Skills for machine-learning study, book-guided reading and evidence-aware experimentation.

[中文说明](README.md) · [Installation](docs/INSTALLATION.md) · [Examples](docs/EXAMPLES.md)

The collection combines a study coach, ML/DL and mathematical foundations, practical evaluation workflows, and reading navigation for eight textbooks. It asks learners to explain, modify and diagnose instead of treating an assistant-generated answer as mastery.

The public package contains original instructions and blank templates. It does **not** redistribute textbooks, extracted passages, private chapter notes, model weights, personal progress or an installed training environment. Book skills guide source selection and reasoning; they are not full-text replacements for the books.

## Install

Git and Python 3.10+ are required for this route. The tools use only the Python standard library.

```sh
git clone https://github.com/superlightliu/ml-dl-skills.git
cd ml-dl-skills
python -B scripts/validate.py
python -B scripts/install.py --dest ../my-project/.agents/skills
python -B scripts/install.py --dest ../my-project/.agents/skills --apply
```

Choose your own destination. Installation is a dry run unless `--apply` is supplied. Install all 11 skills together so sibling references work. Conflicting files are not overwritten. See [installation details](docs/INSTALLATION.md) for manual and plugin routes.

Example: `Use $ml-dl-study-coach to assess my starting point with one question, then propose a realistic study plan.` Responses can be requested in Chinese, English or both.

No GPU, API key or ML package is required to read the instructions. Code execution needs a user-selected environment and task-specific dependencies. External reading requires browsing capabilities or user-supplied material. The package includes no telemetry or background service.

## Development

```sh
python -B scripts/validate.py
```

For installer regression tests, first set the dedicated test directory described in [contribution guidance](CONTRIBUTING.md#本地检查). See [contribution guidance](CONTRIBUTING.md), [security guidance](SECURITY.md) and [third-party attribution](THIRD_PARTY_NOTICES.md). This is an independent project; a GitHub release is not approval or listing by a platform's official directory.

Original repository files are MIT-licensed. Linked textbooks and upstream material retain their own rights and terms.
