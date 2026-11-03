# The Stack — Lydia's design, dictated Oct 30, 2026 (capture, her order)

1. **Informed agent.** We tell an agent a lot of information: the problems we've
   noticed (from the baseline), we explain how models can't always catch
   heuristics, etc. This is a variable to play with — more information might
   make it more accurate or less accurate.

2. **Checker.** The informed agent's output goes to a checker, to check the
   accuracy.

3. **Scramble + topic guess.** Then we mix up the words — including the words
   in the answer choices. The scrambled version goes to a NEW model. That
   model guesses the topic.

4. **Evaluator.** The evaluator is given descriptions of Easy, Medium, and
   Hard questions OF THAT SKILL TYPE. It's told what it needs to be told —
   part of that is the word cloud and the bias check. Then it derives a
   rating.
   - The word cloud (the item's scrambled words, choices included) shows the
     evaluator the item's raw surface — its topic and vocabulary with no
     structure and no solution path — the first-glance signal.
   - The bias check: using the guessed topic and the word cloud, the
     evaluator checks whether that first impression is pulling the rating —
     whether the rating reflects the item itself or the snap reaction to its
     surface.
   - The evaluator is ESPECIALLY told that its job is to predict bias. The
     evaluator is the one that considers the heuristics. Examples (NOT an
     exhaustive list): Abraham Lincoln; Suffragette; "systems of equations
     are to be solved"; etc.
   - As a step, the evaluator tries to determine whether there IS a bias
     challenge in the item. Sometimes there isn't one.
   - The evaluator is also told the green-model fact: a fresh ("green")
     model judging these questions is wrong at kappa 0.256, and it is
     usually wrong in the easier direction (it under-rates difficulty).
     The evaluator holds this as knowledge about its own kind's judgment.
   - If the evaluator is not sure, it can do one of two things (or both):
     (a) using the word cloud and the guessed setting, use the predictive
     nature of AI reasoning to predict reasonable assumptions; and/or
     (b) query the internet for a zeitgeist appraisal.

5. **Bracketing.**
   - If the result is Medium: another agent finds examples to bracket the
     question — harder than this one, easier than this one, similar to this one.
   - If Hard: it only does Medium and Hard.
   - If Easy: it only does Medium and Easy.

6. **Return.** The bracketed result goes back to the evaluator — either the
   original evaluator or a new one. (Open choice.)

**The answerer and the example-fetcher (added Oct 30, later in the session).**
The answerer does these things: it answers the question, it answers "what is
the domain and skill?", it gives a TENTATIVE rating, and it DETAILS ITS
PROCESS. The evaluator can use the answerer's detailed process to pick up
on difficulty as well.
- Token-trace confrontation (Lydia's wording): tell the answerer something
  like "You used X many tokens. The average token use for an easy question
  of this nature is X. Why did you use fewer or more?" The deviation from
  the per-skill band average is the hard datum; the answerer has to explain
  the gap. A new agent then
goes and fetches examples — Easy, Medium, and Hard — and decides whether the
answerer got the DOMAIN AND SKILL right (not the rating — the rating is the
evaluator's job). If there is disagreement, they can go back and forth.
THOSE fetched examples are the examples the evaluator is given (step 4's
skill-type descriptions take this form), so the evaluator's cognitive load
is less.
Correction (Lydia): the evaluator is NOT given the tentative rating. The
tentative rating is only there to help pull the comps. The evaluator derives
its rating without it.
Note: this fetching happens BEFORE the evaluator and is distinct from the
bracketing in step 5, which happens after the evaluator's rating and stays
within the neighboring bands.

Eventually (Lydia, Oct 30, future scope for the app): students answer the
3 review questions (why I didn't choose the right answer; why I chose the
wrong one; why I can do better next time), and a log is kept of why
students get a question wrong.

Presentation note (Lydia, Oct 30): an app students interact with is not
impressive on its own — not without the context of what is typical. The
green model's numbers (50.8% agreement, kappa 0.256, errors leaning easier)
are the context that makes the stack's numbers mean something. The
presentation has to carry the baseline comparison, not just the app working.

Condition Lydia set for the informed-judging test (Oct 30): if Smittens
rates the population sample, it will consider bias AND polarity — the snap
distortion and its direction, whether the surface makes the item read
harder than it is or easier than it is.

Open variables Lydia named: how much information the first agent gets;
original vs new evaluator at step 6.

Build-and-test principle (Lydia, Oct 30): when we create it, we can also be
testing it. The variables are the things the agents are TOLD — each
instruction is an ingredient that can be added or taken out and measured.
Lydia's examples: telling the agent to "solve as a typical student" might
increase rating accuracy; telling the agent to "consider if there are
shortcuts" might increase rating accuracy. Maybe if we take something the
agent is told out, the rating gets more accurate.

Open consideration (Lydia, Oct 30, raised as a question, not decided):
some things are easier because students are clever. Bias runs in both
directions — traps make an item harder than it looks, and student
cleverness (shortcuts, side doors, working back from the choices) makes an
item easier than the intended path looks. The College Board's bands price
in what students actually do, both ways. Question: does the evaluator's
bias prediction need to hunt for student cleverness as well as traps?

---

**Revisions — Lydia, Oct 31, 2026 (these supersede the Oct 30 capture above
where they differ):**

1. The informed agent itself gives the tentative rating (there is no
   separate answerer agent) and shows its process. The tentative rating
   exists for step 3 (the fetcher).
2. The checker checks the informed agent's work.
3. The fetcher finds Easy, Medium, and Hard examples of the domain/skill
   and concurs or disagrees with the domain/skill call. If it disagrees,
   agents 1 and 3 discuss. If neither moves, go with the fetcher, but note
   the informed agent's reason.
4. The scramble produces a snap-judgment topic AND develops a potential
   list of heuristics the item might be trading on.
5. The evaluator is given everything except the tentative rating. The word
   scramble and the heuristics list are just one of its tools, not its main
   tool for its main job. Bracketing is a gated job, done only after the
   rating: Easy needs an Easy and a Medium comp (2); Medium needs three
   comps (easier, similar, harder); Hard needs two (Medium and Hard).


## Agent names (Lydia, Nov 1, 2026)

- **Sol** — the Solver (informed agent)
- **Vera** — the Checker
- **Comp** — the Fetcher (fetches comps)
- **Snap** — the Scrambler (snap topic + heuristics)
- **Val** — the Evaluator (final rating, bias prediction)

Bracketing is a step, not an agent; it returns work to Val.


## Design change (Lydia, Nov 1, 2026): Vera absorbs Comp

The Checker (Vera) takes over the Fetcher's job. Vera: (1) verifies the answer Sol marked right is right and the ones marked wrong are wrong; (2) checks domain and skill; (3) to do that, Vera pulls the comps itself. Comp is no longer a separate agent — pulling comps is a tool Vera uses, not a separate judgment. Named agents now: Sol, Vera, Snap, Val.

Refinement (Lydia, same conversation): Sol's domain and skill call really just tells Vera where to look first. It is a pointer for Vera's comp pulling, not a claim Vera defers to; Vera verifies from there.


## Standing principle (Lydia, Nov 1, 2026)

When we run this stack, we do not know the ground truth, because the job is to derive it. No agent sees the key for the question in front of it. Labels exist only on the outside, for scoring afterward, and reporting must not speak as if the pipeline knew them while it worked.


## Similarity comps — PARKED (Lydia, Nov 1, 2026)

Similarity-based comp retrieval (checking the bank for questions similar to the one at hand) is on the back burner: it looks like a big token spend, and it may belong at a later stage of the stack, only if it is needed. Design constraint if it ever returns (Lydia's ruling in the same conversation): deciding similarity is a judgment, so the runner may only retrieve candidates by mechanical rules; the similarity judgment itself belongs to an agent, out loud, on the transcript.


## Val design input (Lydia, Nov 1, 2026)

The final agent (Val) CAN pull more comps if she wants, at her own discretion — beyond the comps already in front of her. Same mechanical kind as Vera's: a label pull, examples chosen at random from the named domain/skill. Vera's own domain/skill comps stand as-is: random examples by label, no similarity judgment involved, and that is fine.


## Val spec v2 (Lydia, Nov 2, 2026)

Full spec: files/val-design-2026-11-02.md. Val gets everything Lydia would give her for a newly written question she wanted sorted and evaluated: the question, Sol's transcribed process (never Sol's tentative rating, and never the official labels), the surmised domain and skill, Easy/Medium/Hard comps for that skill, the Easy/Medium/Hard descriptors write-up, and Snap's scramble plus surmised topic. She runs her own judgment and supports it by bracketing against the comps (a Medium explains why it is harder than the Easy comp and easier than the Hard comp). She must ask whether the correct answer cuts against a bias a typical 17-year-old might have (reference student: an AP student in pre-calculus; worked example: Lincoln admonishing abolitionists). Her considerations include inverse displays (pH vs acidity, altitude vs temperature), dates out of chronological order, non-deductive elimination inference, a strong distractor placed before the answer, the subtle catch in an easy-looking question (parallel lines posed as a system of equations), and wit, metaphor, or symbolism. Elements can appear at any band; a Hard question may have only one, but so counterintuitive it dominates. Governing standard: a question is hard if students are likely to get it wrong, not if it is difficult to work out. This moves bracketing into the judgment's support, superseding the Nov 1 gated after-step. Confirmed by Lydia (Nov 2, 2026): the comps are always all three bands, because a band-selected comp set would leak the rating — hand Val only Medium and Hard comps and she will realize the question was called Hard. "Give it all 3." Val gets the surmised domain and skill; not the surmised rating; not the actual domain, skill, or rating.


## Snap spec (Lydia, Nov 2, 2026)

Full spec: files/snap-design-2026-11-02.md. The runner mechanically removes the "to be" verbs, the articles, and the prepositions from the question and choices, then scrambles the remaining words. Snap does not unscramble and does not answer; Snap simulates a student's projected topic: 1–2 words typically, 3 if needed ("Staged Play"; for math, area + topic: "Geometry polygons," "Trigonometry radians"). Not about accuracy: it predicts what a tired 17-year-old under time pressure might surmise. Some math scrambles will be just numbers and operations; Snap's brief says that is okay, because some students literally see it like that. If Snap cannot find even 2 words, it flags the item and the runner asks Lydia for direction rather than inventing a snap; that part is provisional and may need finessing.
