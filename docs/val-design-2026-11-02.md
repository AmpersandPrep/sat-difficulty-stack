# Val — the Evaluator: spec v2 (Lydia, Nov 2, 2026)

Val is the final agent; she makes the stack's rating. This spec is Lydia's dictation of Nov 2, 2026. It supersedes the Nov 1 Val design where they differ; differences are flagged at the end. Val remains fresh per question, with no memory of other questions.

Build status: BUILT Nov 2, 2026 (hidden_files/solver-run/val.py), at Lydia's direction. Input packets for all 10 working-set items assemble locally with Sol's tentative rating mechanically stripped (strip logs recorded per packet); Val has NOT been run yet and no tokens have been spent on her.

## The sorting premise

Give Val everything Lydia would give her if Lydia had written a question new and wanted it sorted and evaluated. A new question has no official rating, domain, or skill, so Val never receives the College Board's labels for the question in front of her. Sol's tentative rating is also withheld; Val never sees it.

## What Val receives

1. The question and its choices.
2. Sol's transcribed process: the full transcript of Sol working the question.
3. The surmised domain and skill (Sol's call, as carried in the process). Lydia's exact taxonomy (Nov 2, 2026): surmised domain and skill, yes. Not the surmised rating. Not the actual domain, skill, and rating.
4. The comps: Easy, Medium, and Hard example questions for that skill, with their College Board ratings (labels belong on the comps; they are other questions).
5. The write-up of what makes a question Easy, Medium, or Hard. As built, this is the Methodology section of Lydia's Ela Sharma book document (difficulty-descriptors-v2-ela.md, extracted verbatim), which Lydia directed Smittens to use on Nov 2, 2026, because its write-ups are grounded in College Board's own materials and classifications. It replaces difficulty-descriptors-v1.md, which was Smittens's own Oct 26 prior; Lydia flagged its Medium entry's "exactly one complication" as fake precision, and the v1 file no longer feeds Val's brief.
6. Snap's word scramble and Snap's surmised topic, with the heuristics list.

## The reference student

Val judges for a typical 17-year-old, presumed to be an AP student in pre-calculus: a strong student, not a struggling one. The question Val asks is never "did I find this easy, medium, or hard." It is "would that student."

## The standard

A question is hard if students are likely to get it wrong, NOT if it is difficult to work out. Those are not always the same thing.

## Val's job

1. **Run her own judgment.** Val rates the question herself.
2. **Support it, by bracketing.** A model will tend to just add up the logical deductions and inferences and then make a judgment. Val needs to do more than that tally. She needs to consider the process the solving took (Sol's transcribed process, in front of her), and she needs to consider the comps comparatively: if she calls the question Medium, she explains why it is harder than the Easy comp and easier than the Hard comp; the same comparative support applies at the other bands.
3. **Ask the bias question.** Does the correct answer cut against a bias a typical 17-year-old might have? Worked example: a student carries an impression of Abe Lincoln as an abolitionist. If the passage is about Abe Lincoln admonishing abolitionists as a senator, that cuts against the typical heuristic, and that increases the difficulty.

## The counterintuitive considerations (Lydia's list, Nov 2, 2026)

Val takes note of things like these:

- **Inverse displays.** A graph of pH that then asks about acidity: the graph goes up as the acidity goes down. Altitude paired with temperature: one goes up, the other goes down. Presenting a quantity through its inverse raises difficulty.
- **Dates out of order.** Dates presented out of chronological order are a consideration.
- **Non-deductive inference.** An inference or conclusion that is not straight deductive logic, more "if it's not this, then we can presume it's not that" than "if this, then that," is more difficult.
- **A strong distractor early.** A strong distractor placed before the correct answer in the order can increase difficulty.
- **The subtle catch in an easy-looking question.** That is difficult in itself. Example: parallel lines presented as a system of equations, without saying parallel lines. It challenges a heuristic, because students who got good grades have typically solved a lot of systems of equations, and there is no solve for parallel lines.
- **Wit, metaphor, symbolism.** Where there is wit, metaphor, or symbolism, the difficulty increases.

Calibration on the whole list: Easy and Medium questions will still have these elements. A Hard question may only have one of them, but it is so counterintuitive that it dominates. Presence of an element is not the verdict; degree is.

## What Val passes on

- Her rating.
- The support: the comparative bracket against the comps, and the bias determination (whether the correct answer cuts against a typical student's bias, and how).

## Differences from the Nov 1 design, and carried-over items

- **Bracketing moved.** Nov 1 had bracketing as a gated step after the rating, with comps sized by the rating. Nov 2 puts Easy, Medium, and Hard comps for the skill in Val's inputs up front and makes the bracket comparison the support for the judgment itself. The Nov 1 after-step is superseded unless Lydia says otherwise.
- **Carried over, not mentioned Nov 2:** Vera's output (verified answer, verified domain/skill, notes) as an input; Sol's and Vera's token counts as traces; the green-model fact (fresh model at kappa 0.256, errors leaning easier) in Val's brief; Val may pull more comps at her own discretion. These stay unless Lydia strikes them.
- **Labels point, confirmed by Lydia (Nov 2, 2026):** surmised domain and skill, yes; not the surmised rating; not the actual domain, skill, and rating. And the comps are always all three bands, Easy, Medium, and Hard, for exactly this reason: a comp set selected by band would leak the rating. If Val were handed only Medium and Hard comps, she would realize the question was called Hard. "Give it all 3." This settles the bracketing question too: the Nov 1 gated, rating-sized comp pull is out, because the pull itself was a tell.
