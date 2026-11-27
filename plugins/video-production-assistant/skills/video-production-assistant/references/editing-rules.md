# Cut craft

These are defaults. `edit_rules.md` in the user's video library overrides them.

## Pauses and fillers
- Long pauses: shorten to about 0.15-0.25 s, do not remove fully. Zero-gap joins sound breathless.
- Keep the pause before a key point or after a question. Raise `--keep-pause` or restore that cut.
- Fillers ("um", "uh", "er") go. Keep "so", "right", "you know" unless the user asks; removing them often breaks the sentence.
- Breaths: a breath before a sentence is natural. Do not chase every breath.

## Retakes and false starts
Read the transcript for:
- the same sentence said twice or more (keep the last complete, fluent take unless an earlier one is clearly better);
- "sorry", "let me start again", "cut that", "one more time";
- a sentence that stops halfway and restarts.
Mark the unwanted take's segment `"keep": false, "reason": "retake - kept later take at m:ss"`. If a retake starts mid-segment, split the segment: copy it, set the first copy's `end` and the second copy's `start` at the retake point (use word timings from `words.json`), then drop the right part. List every judgement cut for the user with time and words.

## Jump cuts
A cut in a static talking head makes the head "jump". Fine for YouTube pace; distracting in calm training. Ways to hide them, in order: cut away to B-roll over the join; punch in (scale the A-roll by 10-15% on alternate segments with an overlay of a cropped copy); or accept them.

## Pacing for teaching
- Change the picture when the idea changes, not on a timer.
- Hold screen shares long enough to read: about 2 s plus reading time for any new text.
- Zoom into the part of the screen being discussed (crop the screen share) rather than showing the whole desktop.
- A chapter card or lower-third title at each new section helps people who skip around.

## Openings and endings
- Start on the first useful sentence. Cut "hi everyone, can you hear me".
- The hook (first 15-20 s) says what the viewer will be able to do by the end.
- End within 5 s of the last useful sentence, plus any call to action.
