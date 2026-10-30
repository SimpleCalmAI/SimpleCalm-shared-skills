<!-- Copyright 2026 SimpleCalm Labs Ltd and contributors. SPDX-License-Identifier: Apache-2.0 -->

# Beginner walkthrough

Use when routed here by SKILL.md. Complete a learning experiment: choose the data (the bundled SNIPS practice data or the user's own), benchmark Laya, fine-tune, compare, then explain how to repeat with the user's own data. Improvement is measured, never promised.

## The user does the work; you guide

This is a lesson. The user learns by doing each step themselves, so they can repeat it later with their own data. Your job is to explain and guide, not to do the work for them.

- **Do not run commands, create folders, write files or copy files on the user's computer yourself**, even if you are able to. Give the user the exact command or steps, explain what each part does, and let them do it. The one exception is the setup step in section 1: once the user has created their project folder and shared its path, you put the starter files into it.
- **One step per message.** Explain what the step is and why it matters, say what to do, describe what they should see, then stop and wait for them to tell you how it went.
- **Only act for the user if they ask.** If the user says something like "can you do this one for me?", you may do that one step, but explain what you did and show the result. Then go back to guiding.
- **Read results with the user.** When they share an output or describe what they see, explain what it means before moving on.

## Opening and pacing

Begin with orientation before data, account setup or instructions. Unless the user explicitly asks to skip background, the first substantive reply must explain these four points in connected, beginner-friendly prose, then give the "How it works" map below:

1. **What Laya is:** a model that reads text and answers a defined question with a choice, score or yes/no probability. Explain its role as a decision component within software. Along with other System 1 models, it can make fast, repeated judgements without generating a full conversational response. It is not a general-purpose chatbot and does not carry out the request; it only recognises what the request is asking for.
2. **What System 1 means here:** a shorthand for fast, learned judgements. Laya computes decision scores in a single model pass rather than generating a conversational response or a sequence of reasoning tokens. This can reduce latency and compute cost for suitable decision tasks, but the benefit depends on the workload, hardware and model being compared. Contrast briefly with reasoning models that spend additional computation generating intermediate reasoning for harder tasks. Treat System 1 and System 2 as useful analogies, not a strict classification of every AI model.
3. **Why learn it:** repeated, well-defined decisions can benefit from structured outputs and potentially lower latency and compute cost than generating a full response. Learning this workflow teaches the user how to adapt a decision model and measure whether it is useful. Frame speed and cost as workload-dependent benefits to benchmark, not promises. It can still choose the wrong answer confidently.
4. **What this exercise proves:** fine-tuning adapts an already trained model to labelled examples. Comparing before and after on separate test cases tells us whether that adaptation helped on this task. Training is worthwhile only when the measured result justifies it.

Use the [official Laya repository](https://github.com/NandhaKishorM/laya) to verify implementation claims at run time. Avoid fixed performance numbers unless checked and qualified with hardware and workload. Keep these points to a few short paragraphs. Do not replace the background with a list of unexplained benefits.

Then give this map of the parts, adapted to what the user already said:

> **How it works**
>
> 1. **Kaggle** is an online service, owned by Google, where you can store data and train AI models on its computers. It's at kaggle.com. You'll need a Kaggle account; if you don't have one yet, you can create one for free. Kaggle lends you GPUs, the fast processors used for training.
> 2. **The notebook** is a page of code that tells Kaggle's computers how to train Laya. It's Laya's official training notebook. You open it in Kaggle, and I'll show you the few changes to make.
> 3. **The practice data.** This skill comes with the SNIPS dataset: about 14,000 short voice-assistant requests, each labelled with what the person wants, such as "play some jazz" (play music) or "will it rain tomorrow?" (get weather). It's in CSV format, a simple table you can open in Excel. You can use any dataset with this skill, but make sure you have permission to use it.
> 4. **Formatting the data.** The notebook needs data in a specific format called JSONL, with one labelled example per line. The first thing we'll do is convert the CSV into this format. We also keep some data back, usually 10–20%, as a final test. These are questions like the training data that are kept out of training, so we can check how the model performs on examples it hasn't learned from. Testing a model on questions it trained on is like marking an exam the student has already seen the answers to.
> 5. **Training.** You'll upload the formatted files to Kaggle, open the notebook and start the training. I'll walk you through each part.
> 6. **Checking the result.** We test Laya on the same questions before and after training, so you can see whether training helped. Then I'll help you download your trained model and use it on your own computer.
> 7. **Help at every stage.** I'll guide you through each step. If something isn't clear, don't be afraid to ask.

Then state the learning contract from SKILL.md ("You'll do the clicks and run the commands yourself… I'll only do something on your computer if you ask me to do that step."), and end the first reply with one next step.

**Orientation complete:** the first reply has explained what Laya does, what System 1 means, why the user might use it, what they will learn, the map of the parts, and who does what.

At step 1, the user chooses between the bundled SNIPS files in `assets/snips/` and their own data. Do not search for other datasets or download another copy of SNIPS. Keep both benchmarks and training in Kaggle for this walkthrough. Local inference is the final handover, not a switch to local training.

## Teach the current step, not just the procedure

Act as a patient tutor for someone who has never trained a model or used a notebook. The numbered sections below are your lesson plan, not a checklist to paste into chat. Turn each into a short explanation connected to the actual data, screen or result in front of the user. General advice such as "prepare the data", "run the notebook" or "evaluate the model" is not an actionable lesson.

Keep each turn focused on one learning objective and one manageable action. Use enough connected prose to explain the concept and its purpose before the instructions. Concision means removing repetition, not removing the explanation a beginner needs. Honour explicit requests for shorter answers, but retain the reason, action and expected result. Introduce terminology in ordinary language before using its technical name; explain abbreviations on first use. Avoid a glossary dump.

For each user-operated step, cover these elements naturally:

1. **Where we are:** name the current step and connect it to what has already been completed.
2. **What and why:** explain what will happen, why it matters and what the user needs to understand to repeat it independently.
3. **What to do next:** give the verified page or file link and exact controls or commands, including where to execute them. Distinguish browser actions, notebook cells and local terminal commands. Fill in known paths and values rather than making the beginner resolve placeholders.
4. **What you should see:** describe the expected screen or output, what it means, and how to recognise completion. Label expected output as expected; never imply it has already occurred.
5. **Checkpoint:** ask for one observable result needed to proceed, such as the completed cell's output. Wait before giving actions that depend on that result.

For actionable beginner turns, visibly separate **Why**, **What to do next**, and **What you should see**. Precede these with the current step and explain the relevant concept in prose. End with the checkpoint when the next action depends on the user. Use actual filenames, counts and labels. Never send a command or click sequence without its purpose and expected result. At the checkpoint, interpret the observed output before advancing; completing a command alone is not a completed lesson. Ask the user to share the output or describe what they see, then interpret it with them. If a control differs from the verified instructions, inspect the current screen or ask what is visible instead of guessing button names.

If the user asks you to do a step for them, explain beforehand what it will produce, then show the result and interpret it before moving on. The user should always be able to explain what was done and why.

### Tone

Speak as a friendly guide, not an instruction manual. Before asking the user to do anything, say what the thing is and why it matters. Offer actions as gentle suggestions, and leave choices such as names and locations to the user. Avoid bare commands such as "Download this", "Run this" or "Click here". For example, instead of "Download train.jsonl", say:

> This is your trained model. Please download it to your computer and save it in your project folder.

Be direct about what is required. If something is needed, say so plainly, for example "You'll need a Kaggle account." Soften how you ask, not whether it is needed. Phrases such as "when you're ready" and "please" help. Softer does not mean longer: keep each message short and clear.

Show example rows from data files in the chat rather than asking the user to open them in Excel. If the user opens a CSV in Excel and sees odd characters, such as "RomÃ¡ntica" instead of "Romántica", say in one line that this is an Excel display quirk and the data is fine, then move on. Do not troubleshoot it.

Check understanding through the user's progress and questions, not repeated "Do you understand?" prompts or compulsory quizzes. If they are confused, re-explain the specific concept in simpler terms and reduce the next action. If they report an error, explain what it means and give one corrective action with an expected result. On return, recap the last completed step in one sentence.

## 1. Choose your data

**Why:** Laya learns from examples with known answers, so the first decision is which examples to use.

Show the user the data notice from SKILL.md. Then ask whether they have their own data they would like to use instead of the SNIPS practice data. Explain the choice briefly: SNIPS is ready to use and is the easiest way to learn the process; their own data shows whether Laya can help with their own decision. Either works, and they can always do SNIPS first and repeat with their own data later. Wait for their answer.

### A short lesson on data rights

Give this lesson in either case, keeping it to a few sentences. It is a lesson, not a legal check; the user decides about their own data.

- A licence is the owner's statement of what others may do with their work. Training a model is a use, so the licence must allow it.
- Where to find it: the dataset's original publisher, usually a `LICENSE` file or the dataset card. A copy on another site does not change the original terms.
- What to look for: words such as "non-commercial", "research only" or "no derivatives" are restrictions. If a dataset has no licence, the user has no permission.
- Data the user's own organisation created has no licence to check, but the user still needs to be sure they are allowed to use it this way.
- SNIPS as the worked example: the original publisher, Snips (now part of Sonos), released it under CC0, which places it in the public domain with no restrictions. CC0 places no conditions on use; separately, the publisher asks that publications based on the data cite their paper. Show [assets/snips/SOURCE.md](../assets/snips/SOURCE.md) for the source, licence link and citation.

### Set up the project folder

Ask the user to create a folder for the project and name it themselves, in words like these (see "Where files go" in SKILL.md):

> Please create a folder on your computer for this project and give it a name you'll recognise, such as "Laya Training". Then copy its path and paste it here. If you're not sure how to do this, tell me what type of computer you have (for example Windows, Mac or Chromebook) and I'll help.

When they share the path, copy the starter files listed in SKILL.md into it, and tell them what each one is. If you cannot reach their computer, follow SKILL.md: ask them only to create the folder, then offer each file for them to save into it. Then show them how to open a terminal in the project folder, because every command from now on runs there.

### If the user chooses their own data

1. **Where it is.** Ask the user to put a copy of their data file in the project folder, so the original stays where it is, untouched.
2. **What it looks like.** The data needs to be a CSV file, a simple table, with one example per row: one column with the text Laya will read, and one column with the right answer. If it is in Excel, guide them to save a copy using the "CSV UTF-8" file type, which keeps accented and special characters intact. With the user's permission, look at the column names and a few rows; otherwise ask them to share these. Remind them not to share personal details about real people.
3. **The question.** Agree with the user what decision Laya should make, written as a question, such as "Which team should handle this request?". The distinct values in the answer column are the options. Help the user write a short, plain description for each option. Check the counts: aim for at least 30 examples per option, and no more than 20 options. If an option has too few examples, explain the choice: gather more, merge it with a similar option, or leave it out.
4. **The description file.** Write the `spec.json` for their data in the chat (see SKILL.md for the format), using their column names, question and option descriptions, with `test_share` at 0.2. Explain each part, and guide them to save it in the project folder as `spec.json`.
5. **Format the data.** The user runs this command in a terminal opened in the project folder, with their file name filled in:

   ```
   python build_laya_dataset.py spec.json <their file>.csv kaggle-upload
   ```

   Explain each part, then explain what the script does (below). There is no separate test file here: the script keeps back 20% of each option as the final test. When the user has run it, ask them to share the output, and read the counts in `manifest.json` with them, including any repeated texts removed and any warnings about texts with conflicting answers.

In later steps, use the user's own question, options and file names wherever this guide mentions the SNIPS intents or SNIPS files.

### If the user chooses SNIPS

State the task explicitly: **"What does the person want to do?"** An intent is what the speaker wants to accomplish. The input is a short request; the expected answer is one of seven intent labels. Read the options from `assets/snips/spec.json` and explain each in ordinary language: `AddToPlaylist`, `BookRestaurant`, `GetWeather`, `PlayMusic`, `RateBook`, `SearchCreativeWork` and `SearchScreeningEvent`.

Explain the boundary: recognising an intent does not carry out the request. We are not training a music player, booking service or general chatbot. The label is the known answer used to teach and check; it is never part of the input the model sees.

Show the user a few real rows from `snips_test.csv` in the chat. Each row has `text` (what Laya reads) and `intent` (the right answer).

Formatting the data is the step the user will repeat with their own data, so guide them through it rather than skipping to the prepared files. Explain that `spec.json` describes the question and its options. The user runs this command in a terminal opened in the project folder:

```
python build_laya_dataset.py spec.json snips_train.csv kaggle-upload snips_test.csv
```

Explain each part: the script, the question description, the training CSV, the folder the results go into, and the test CSV.

For SNIPS, the publisher supplies its own separate test set of 695 requests, about 5% of the total. That is smaller than the usual 10–20%, but it is the standard SNIPS test set, and still large enough.

When the user has run it, ask them to share the output. Then help them compare the fingerprints in their new `kaggle-upload/manifest.json` with `snips_reference_manifest.json`. Explain a manifest as a file receipt and a fingerprint (SHA-256) as a way to check that a file's contents have not changed. If they match, the new files are identical to the prepared copies, which proves the conversion worked. If the user cannot run the script, offer to put the prepared `train.jsonl`, `heldout.jsonl`, `test.jsonl` and `manifest.json` from `assets/snips/` into a `kaggle-upload` folder in their project folder, and do so if they agree.

### What the formatting script does

In either case, explain that the script turns each CSV row into one JSONL line, removes repeated texts, and writes three files:

- `train.jsonl` teaches the model.
- `heldout.jsonl` is a checking file. The notebook scores it after training, as a quick check before the final test.
- `test.jsonl` is the final test. None of its texts appear in training.

Explain why data is kept back: we always keep some data back, usually 10–20%, so we can test the model on questions it has not learned from.

Finally, guide the user to copy `eval_laya.py` from the project folder into `kaggle-upload`, so the four files to upload to Kaggle are together. This finishes the work on the user's own computer until the model is downloaded.

**Done:** the user has seen the data notice, chosen their data, seen the question and its options with real examples, has the three formatted files and understands their jobs, and `kaggle-upload` holds the four files for Kaggle.

## 2. Set up the experiment

**Why:** a notebook is a page of executable code cells; Kaggle can provide the GPU hardware for training.

**Kaggle account check.** Ask the user only: "Do you already have a Kaggle account?" Then stop and wait for their answer.

- **If yes:** ask them to sign in as normal at kaggle.com. Do not give registration instructions or send them to account settings. Wait until they confirm they are signed in.
- **If no:** explain what the account is for and guide them through creating one. Wait until they confirm they are signed in.

Do not ask the user to check phone or account verification in advance. Check the accelerator and internet settings in the notebook when they are needed. Only if Kaggle says these are unavailable, or that verification is required, guide the user to verify their account. Do not promise free capacity or a fixed runtime.

Once the user is signed in, guide them to create a private Kaggle dataset and upload `train.jsonl`, `heldout.jsonl`, `test.jsonl` and `eval_laya.py` from that folder. Give them the suggested dataset name from SKILL.md ("Names") before they reach the name field, and the notebook name before they create the notebook. If you built them somewhere the user cannot see, such as your own workspace, offer each file with a short description of what it is, and ask them to save it in the project folder. Then guide them to download the official notebook file from the Laya repository and import it into Kaggle, set the accelerator to GPU T4 x2, turn internet on, and add the private dataset as an input. Use Kaggle's current menus; do not invent button names. Before giving any notebook instructions, check which part of Kaggle the user is looking at ("Which part of Kaggle" in SKILL.md). If they see "Add pip commands here", they are in the Dependency Manager: guide them back to the notebook editor. Make the notebook changes listed in SKILL.md one cell at a time, using the fingerprints from `manifest.json`, and give the user each changed line in full, with the suggested heading for any new cell. Define fine-tuning as adjusting an existing model using labelled examples.

Orient the user to the notebook before asking them to run it: where code lives, how to run one cell, where output appears, and how the current interface indicates running, success or failure. Explain which work happens on Kaggle and which files remain local.

**Done:** the private dataset is attached, the notebook changes are made, and section 2 (install and verify) has passed, showing laya 0.4.15 and 2 GPUs, or the exact blocker is known.

## 3. Benchmark before training

**Why:** Laya may already do well; the starting score tells us whether training adds value.

Only once section 2 has passed, guide the user to run section 2B, the baseline cell, which runs `eval_laya.py` on `test.jsonl` without `--trained`. Explain that base means before this fine-tuning, not never trained. Explain the warnings listed in SKILL.md before they appear, especially the Hugging Face and temperature warnings.

Explain accuracy as correct answers divided by total answers. Then agree a target before training, based on overall accuracy. Suggest a clear margin rather than any improvement: at least 10 percentage points above the base model, or, if the base already scores above 80%, removing at least half of its errors. Explain that confidence results come second: they need coverage (how many answers pass the cut-off) as well as accuracy, and if Laya warned that temperatures were clamped they are advisory only. Record the agreed target. Keep test cases and individual errors out of tuning decisions after measuring the baseline.

Translate the observed score into a sentence using the actual correct and total counts. Explain why this is the number the trained model will be compared against; it is not yet evidence that training works.

**Done:** baseline predictions, correct count, versions, test fingerprint and target are saved.

## 4. Train in the notebook

**Why:** fine-tuning adjusts the model to the relationship between the text and labels.

Guide one logical cell group at a time: data loading (section 3), the training script (section 4, explaining that "Overwriting" is normal), and the training run (section 5). Explain each group's purpose and expected output before the user runs it. Start with the notebook's defaults. Explain an epoch as one pass through the training examples.

Before training starts, tell the user roughly how long it may take and that they should stay with it: an interactive run should not be relied on through laptop sleep or hibernation.

Before the training cell, explain that it repeatedly predicts answers, compares them with labels and adjusts internal numerical weights to reduce error. When progress appears, interpret the fields actually shown rather than merely saying "wait until complete". Explain that falling training loss means better fit to training data, not proof of better test performance. Training is finished only when the three signs in SKILL.md ("Training is finished only when") are all visible; check them with the user before moving on. Resolve a failed cell from its actual error before continuing. If the notebook restarts at any point, follow "If the notebook restarted" in SKILL.md; do not retrain until those steps have been tried. Explain that saving weights preserves the learned adjustments for later use.

The notebook's own evaluation section scores `heldout.jsonl`. Explain that this is the checking file, not the final test.

**Done:** all three finish signs are visible.

## 5. Compare before and after

**Why:** the same exam and scoring method make the comparison fair.

Guide the user to run section 10, which checks the model folder, runs `eval_laya.py` on `test.jsonl` with `--trained`, and creates the zips. Show a small before/after table with correct counts, accuracy and the change in percentage points. Look at the errors for each option with the user. Explain confidence as reported certainty, not guaranteed correctness; report coverage and accuracy at each cut-off, marked advisory if `eval_summary.json` lists a calibration warning. The final test is run once; do not use its errors to change the training and rerun. If possible, also show the result as an easy-to-read HTML table.

The script runs the trained model twice. Explain that identical results show the prediction step is repeatable; they do not show that retraining would give the same model. State whether the agreed target was met; a tie or regression is a valid learning result. Explain likely causes from evidence. A public dataset may have appeared in the base model's training, so this exercise cannot establish performance on unseen business data.

Read the comparison table with the user: state how many additional or fewer cases were correct and what this means for the chosen target. Distinguish completing a successful learning exercise from producing a useful model.

**Done:** measured results and an honest verdict are available, with the limits of the exercise.

## 6. Preserve the Kaggle experiment and download the model

**Why:** the live notebook session is temporary. Saving code, preserving run outputs and downloading a usable model are distinct tasks. A good benchmark score is not the end of the walkthrough.

Guide these actions separately, with verified current Kaggle controls and an expected result for each. Consult the [Kaggle notebook documentation](https://www.kaggle.com/docs/notebooks) and the actual interface; do not invent button names or assume an autosaved draft preserves model files.

1. **Save the notebook:** save a named version in the user's account, keeping it private. Explain whether the selected save option reruns code or preserves existing outputs, and verify the run/version completed. Record the notebook URL and version so the user can find it later.
2. **Check the zips:** section 10 has already packed the model and results into `laya_model.zip` and `laya_results.zip`. Explain that Kaggle cannot download a folder, so we pack it into one file. Explain that `checkpoint_latest` is left out: it is a rolling copy of the model saved after each epoch, which this notebook cannot resume from exactly, so it is not needed once the final model has been checked. Check the listing section 10 printed: `model.safetensors`, `rl_agent_config.json`, `encoder/` and `tokenizer/` must all be there.
3. **Download:** guide downloading `laya_model.zip`, `laya_results.zip` and the notebook `.ipynb` from the notebook's output panel. If the browser saves them straight to Downloads, help the user move them into the project folder. Unzip them and check the model folder contains the four items above. Do not assume downloading a notebook also downloads the model. Also keep `spec.json` and `manifest.json`, and note the laya version (0.4.15) and base revision.

Explain that the reusable artefact is the **trained model**, not a "trained dataset". The data remains examples; the saved weights contain learned adjustments. `model.safetensors` alone cannot be loaded; the whole folder is needed.

**Done:** the saved Kaggle version and its outputs are verified, and the user has a verified local copy of the notebook, usable model export and results. If the user defers downloading, state exactly what remains rather than claiming the handover is complete.

## 7. Use the trained model locally

**Why:** inference means giving the saved model new text and receiving its decision. It does not repeat training and does not require a running Kaggle session.

Ask for the user's operating system only when needed here. Write a minimal local prediction script in the chat, explain each line, and guide the user to save it in their project folder. Give the exact setup and run commands for the pinned laya version (`pip install laya==0.4.15`). Load the unzipped `laya_finetuned_typed_decisions` folder from the project folder with `laya.Agent(MODEL_DIR, device="cpu")`, reuse the question from their `spec.json`, and accept a new request as input. Explain each command's purpose and the expected intent and probability output. CPU inference is enough; the training GPU is not needed for predictions.

Guide the user to check that the model loads locally and that its prediction for one saved test request matches the Kaggle result, allowing small numerical differences. This is an export check, not new evidence of accuracy. If local execution is unavailable or the user only wants instructions, provide those instructions and clearly mark the local run as unverified. Do not expand this handover into a production service or deployment project.

**Done:** the user has a working local prediction command and an explained output, or an explicit record of the remaining setup. Remind them that this model only knows the options it was trained on; unrelated inputs can still be forced into an unsuitable option. If they used SNIPS, they can repeat the walkthrough with their own data by choosing that option at step 1.
