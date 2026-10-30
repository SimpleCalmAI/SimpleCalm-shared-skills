# SimpleCalm AI Shared Skills

Skills and plugins we’ve built at [SimpleCalm AI](https://simplecalm.ai), shared for you to use and adapt.

Some help with practical business tasks. Others help you experiment and understand how AI works. We hope you find them useful.

## Plugins

A plugin is a bundle of one or more skills (and, in future, MCP server definitions) that you install together. Each plugin follows the open [Agent Plugins](https://agent-plugins.org) specification and lives in its own folder under [`plugins/`](./plugins/).

| Plugin | Components |
|---|---|
| [laya-training](./plugins/laya-training/) | 1 skill |

## Skills

A skill is a single set of instructions your AI assistant can follow. You can install a skill on its own, without its plugin.

| Skill | Plugin | What it does |
|---|---|---|
| laya-training | [laya-training](./plugins/laya-training/) | Guides you through fine-tuning and evaluating Laya, a model for focused decisions. Includes a practice dataset and a walkthrough using Kaggle. |

We’ll add more as we develop them.

## Getting started

Choose a plugin or skill from the lists above, then install it in one of two ways. Each plugin’s own README has full instructions and details of any accounts or tools you’ll need.

1. **As a plugin, through Claude Code.** In Claude Code, add this repository as a marketplace, then install the plugin you want:

   ```
   /plugin marketplace add SimpleCalmAI/SimpleCalm-shared-skills
   /plugin install laya-training@simplecalm-shared-skills
   ```

2. **As individual skills, in any coding agent, using [skills.sh](https://skills.sh).** Run this in a terminal (it needs [Node.js](https://nodejs.org)), naming each skill you want with `--skill`:

   ```
   npx skills add SimpleCalmAI/SimpleCalm-shared-skills --skill laya-training -g
   ```

   You can repeat `--skill` to install several skills at once.

## For contributors

Each plugin is a folder in `plugins/` with a `plugin.json` at its root and its skills in `skills/<skill-name>/SKILL.md`. Run `python scripts/validate.py` (after `python3 -m pip install -r scripts/requirements.txt`, ideally in a virtual environment) to check your changes. The same check runs on every pull request. When a pull request that raises a plugin’s version is merged to `main`, a GitHub release is published for that plugin automatically.

## Use them. Adapt them.

These skills are shared as they are, without support. You’re welcome to copy, change and build on them under each skill’s licence.

## Licences and data

Check the licence in each skill’s folder before using or adapting it. Bundled datasets and third-party components may have separate licences.

Use skills responsibly. You are responsible for ensuring you have the necessary rights and permissions to use third-party material with our skills, including permission to use datasets for model training where applicable.

Have fun!
