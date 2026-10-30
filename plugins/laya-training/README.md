<!-- Copyright 2026 SimpleCalm Labs Ltd and contributors. SPDX-License-Identifier: Apache-2.0 -->

# Laya training

A guided skill from SimpleCalm AI for learning how to fine-tune and evaluate Laya, the open-weight System 1 decision model developed by Convai Innovations.

The skill explains each step in plain English, guides a Kaggle experiment with a bundled practice dataset, compares the original and trained models on test questions kept out of training, and helps you save and use the trained model on your own computer. It is an instructional assistant, not a pre-trained model or an automatic training service. Improvements are measured, not guaranteed.

## How it works

1. **Kaggle** is an online service, owned by Google, where you can store data and train AI models on its computers. It's at [kaggle.com](https://www.kaggle.com). You'll need a Kaggle account; if you don't have one yet, you can create one for free. You may need to verify your phone number to use its GPUs, the fast processors used for training.
2. **The notebook** is a page of code that tells Kaggle's computers how to train Laya. It's Laya's official training notebook. You open it in Kaggle, and the skill shows you the few changes to make.
3. **The practice data.** The skill comes with the SNIPS dataset: about 14,000 short voice-assistant requests, each labelled with what the person wants. It's in CSV format, a simple table you can open in Excel. You can use any dataset with the skill, but make sure you have permission to use it.
4. **Formatting the data.** The notebook needs data in a specific format called JSONL, with one labelled example per line. The first thing the skill does is convert your CSV into this format. It also keeps some data back, usually 10–20%, as a final test. These are questions like the training data that are kept out of training, so you can check how the model performs on examples it hasn't learned from. Testing a model on questions it trained on is like marking an exam the student has already seen the answers to.
5. **Training.** You'll upload the formatted files to Kaggle, open the notebook and start the training. The skill walks you through each part.
6. **Checking the result.** The skill tests Laya on the same questions before and after training, so you can see whether training helped. It then helps you download your trained model and use it on your own computer.
7. **Help at every stage.** The skill guides you through each step. If something isn't clear, don't be afraid to ask.

The skill will ask you to create a folder for the project, with a name you'll recognise such as "Laya Training", and to paste its path into the chat. It then puts everything needed for the exercise into that folder, so it's all in one place.

## Your training data

Always make sure you are entitled to use your dataset to train or fine-tune AI models. A trained model keeps what it learned from its data. If you use data you have no right to, you may face legal claims and have to withdraw or retrain the model.

You can use data when you definitely own it, or when you have correctly licensed it for this purpose.

If you do not own the dataset, check its licence and make sure this use is not prohibited or restricted. If in doubt, do not use it.

## Install

### Claude Code (as a plugin)

Inside Claude Code, run:

```
/plugin install laya-training --marketplace SimpleCalmAI/SimpleCalm-shared-skills
```

On Claude Code versions before 2.1.275, add the marketplace first, then install:

```
/plugin marketplace add SimpleCalmAI/SimpleCalm-shared-skills
/plugin install laya-training@simplecalm-shared-skills
```

From a terminal, the same two steps are `claude plugin marketplace add SimpleCalmAI/SimpleCalm-shared-skills` and `claude plugin install laya-training@simplecalm-shared-skills`. Start a new session, then type `/laya-training:laya-training` or ask Claude to "use the Laya training skill".

### Codex and other coding agents

Run this in a terminal (Git Bash, PowerShell, Terminal), not inside the agent. It needs [Node.js](https://nodejs.org) version 22.20 or later; see the [skills installer](https://github.com/vercel-labs/skills) for details.

```
npx skills add SimpleCalmAI/SimpleCalm-shared-skills --skill laya-training -g
```

Choose your agents when asked. The `-g` installs the skill for your whole user account. Without it, the skill is installed only in the folder you ran the command from, and your agent will only see it when opened in that folder. Restart your agent afterwards. Then type `$laya-training` in Codex, or ask your agent to "use the Laya training skill".

### Claude app (web or desktop)

1. Download `laya-training-skill.zip` from the newest `laya-training` release on the [releases page](https://github.com/SimpleCalmAI/SimpleCalm-shared-skills/releases).
2. In Claude, open **Customize** (called **Plugins** on accounts with the newer layout), go to Skills, and upload the ZIP. Enable the skill. Code execution and file creation must be enabled; organisation settings may also apply.
3. Start a new chat and use the prompt below.

If the interface changes, follow [Claude's current skill installation guidance](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

## First prompt

> Use the Laya training skill. I am new to model training. Explain what Laya does, then guide me through the beginner Kaggle experiment one step at a time. Start with what I will learn and the first action.

Please don't upload confidential or personal data to Kaggle or any other service unless you have permission to do so.

## What is included

- **The skill:** step-by-step instructions, a beginner guide, and two helper scripts. One script formats a labelled CSV into training and test files. The other scores the model before and after training.
- **Practice data:** the SNIPS dataset, published by Snips (now part of Sonos) under CC0. See [`skills/laya-training/assets/snips/SOURCE.md`](skills/laya-training/assets/snips/SOURCE.md) for the source. CC0 places no conditions on use; separately, the publisher asks that publications based on the data cite their paper.

Not included: Laya itself, the official training notebook, model weights or a Kaggle account. Laya and the training notebook are maintained in the [official Laya repository](https://github.com/NandhaKishorM/laya). The scripts and instructions have been checked against laya 0.4.15 and the notebook at a fixed version.

## Tested result

The SNIPS practice experiment was run from start to finish on Kaggle (2 × T4 GPUs) on 29 October 2026, with laya 0.4.15 and the reviewed base-model revision. Both models answered the same 695 final-test questions, which were kept out of training.

| Result | Base Laya | Fine-tuned Laya |
|---|---:|---:|
| Correct | 611 / 695 | 688 / 695 |
| Accuracy | 87.9% | 99.0% |
| Errors | 84 | 7 |

Fine-tuning raised accuracy by 11.1 percentage points and removed 91.7% of the base model's errors, passing the target agreed before training (653 correct). Running the trained model twice gave identical predictions.

SNIPS is public, so its test questions may have appeared in the base model's earlier training. Treat this as evidence that the process works, not as a forecast of performance on your own data. Your results will depend on your data.

Not yet verified: running the trained model on your own computer (the final optional step), and the route for your own data, which is new.

## Licence and attribution

Version 1.0.11. Copyright 2026 SimpleCalm Labs Ltd (trading as SimpleCalm AI) and contributors.

This guide, its helper scripts and release documentation are open source under the **Apache License 2.0**. You may use, modify and redistribute them, including commercially, under that licence's terms. Every release includes the complete `LICENSE` and an attribution `NOTICE`. The bundled SNIPS data remains under CC0.

Laya's code, official notebook and published `convaiinnovations/laya` model identify Apache-2.0 as their licence. Laya remains the work of Convai Innovations and its contributors. This guide is an independent project and does not imply their endorsement. See [the licence review](LICENSING.md) for the checked sources and the scope of this release.

The licence for this guide does not grant rights to your training data or to third-party model components. Check the exact files and revisions you download or redistribute, and keep their applicable licences and notices.
