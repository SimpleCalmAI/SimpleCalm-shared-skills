<!-- Copyright 2026 SimpleCalm Labs Ltd and contributors. SPDX-License-Identifier: Apache-2.0 -->

# Licence review for the Laya training skill 1.0.10

Checked on 28 October 2026. This is a review of the files in the SimpleCalm AI skill and plugin release archives, not a legal opinion about every later model, dataset or deployment a user may create.

## Verified upstream terms

- **Laya repository:** [LICENSE at commit fe9a6c35023a7d94102e7feaaeaae8857d9d1b07](https://github.com/NandhaKishorM/laya/blob/fe9a6c35023a7d94102e7feaaeaae8857d9d1b07/LICENSE) contains the Apache License 2.0 terms. The complete repository tree at this revision contains no file named `NOTICE` or a variant of that filename. Separate benchmark licences exist, but no Laya benchmark data is included here.
- **Official training notebook:** [the Kaggle notebook at the same revision](https://github.com/NandhaKishorM/laya/blob/fe9a6c35023a7d94102e7feaaeaae8857d9d1b07/notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb) identifies Apache 2.0 and credits Convai Innovations, as do the repository README and `pyproject.toml`. The notebook itself is not included in this release; the skill describes changes for users to make in their own copy.
- **Published model:** the [convaiinnovations/laya model card](https://huggingface.co/convaiinnovations/laya) declares `apache-2.0`, as did the card at [revision 7b928d828b7b0e022f929d9bd2e44165aa270148](https://huggingface.co/convaiinnovations/laya/blob/7b928d828b7b0e022f929d9bd2e44165aa270148/README.md). The skill loads revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, the reviewed pin in laya 0.4.15 (`laya.PINNED_REVISIONS`); check [its model card](https://huggingface.co/convaiinnovations/laya/blob/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/README.md) before redistributing weights. Model weights and their dependency files are not included in this release.
- **SNIPS practice data:** [sonos/nlu-benchmark LICENSE at commit b86ac7f1577868c42158d0dec77db50956046696](https://github.com/sonos/nlu-benchmark/blob/b86ac7f1577868c42158d0dec77db50956046696/LICENSE) is CC0 1.0 Universal. The repository README states that any publication based on the datasets must include a full citation to Coucke et al., 2018; that citation is reproduced in `NOTICE` and `assets/snips/SOURCE.md`.
- **Licence text:** the release's `LICENSE` is the unmodified [Apache License 2.0 text](https://www.apache.org/licenses/LICENSE-2.0.txt). Its SHA-256 is `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.

## What this release contains

The skill archive contains the `laya-training` skill folder: the training instructions, the beginner guide, the helper scripts in `scripts/`, the converted SNIPS data and its conversion script in `assets/snips/`, `LICENSE` and `NOTICE`. The plugin archive contains the same skill folder plus a plugin manifest, the README, this review, `LICENSE` and `NOTICE`. No Laya implementation, upstream notebook, model weights, tokenizer files or upstream artwork is redistributed.

The helpers call Laya's public API and use its training-row format. Apache-2.0 section 1 distinguishes separable works and interface use from derivative works. On the reviewed file inventory, no conflict with Laya's licence was identified. The SNIPS data is redistributed under its CC0 dedication, with the source and changes described in `assets/snips/SOURCE.md`. These conclusions are limited to these release contents; they do not cover data or model files a user obtains later.

## Our licence

The SimpleCalm AI training guide, helper scripts and release documentation are licensed under Apache-2.0 by SimpleCalm Labs Ltd (trading as SimpleCalm AI). This is a permissive open-source licence allowing commercial use, modification and redistribution, with the copyright, patent and redistribution terms in `LICENSE`. Choosing the same licence as Laya keeps the release terms consistent; Laya's licence does not require independent guides to use the same licence. The bundled SNIPS data is not relicensed; it remains under CC0.

Credit is retained in `NOTICE` and the README. Names are used to identify the upstream project and data publisher, without suggesting endorsement. Copyright and SPDX identifiers accompany the skill, guide, release documentation and scripts. Data files (`.csv`, `.jsonl`, `.json`) carry no headers; their status is set out in `NOTICE` and `assets/snips/SOURCE.md`.

## If upstream files are added later

Apply section 4 to the actual files being redistributed: include the licence, retain relevant copyright and attribution notices, mark modifications to upstream files, and reproduce any relevant upstream `NOTICE` content. The guide's licence cannot relicense third-party material.

For applying the licence to a project, see the [Apache Software Foundation's licensing FAQ](https://www.apache.org/foundation/license-faq.html#Apply-My-Software). This review does not change the licence terms.
