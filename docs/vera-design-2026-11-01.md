# Vera — the Checker (design, Nov 1, 2026)

Vera is the second agent. Per Lydia's Nov 1 design change, Vera absorbs the old Fetcher job: Vera pulls the comps itself. Sol's domain and skill call tells Vera where to look first — a pointer, not a claim Vera defers to.

## What Vera receives

- The question and its choices.
- Sol's full transcript: the worked process, the per-choice verdicts with reasons, and Sol's answer, domain, and skill.
- NOT Sol's tentative rating. The rating isn't Vera's business; she never rules on it, and she strips it from anything passed onward (Val never sees it).

## Vera's three checks

1. **The right answer is right.** Vera re-derives the answer herself rather than trusting Sol's reasons, and confirms Sol's marked-right choice actually satisfies the question.
2. **The wrong answers are wrong.** For each choice Sol marked wrong, Vera confirms it fails, and why. If any "wrong" choice turns out defensible or right, Vera flags it: that changes what the question is.
3. **Domain and skill.** Vera pulls comps first from the domain/skill Sol named — real bank examples of that skill, one per band, with their College Board labels, drawn from the accessible bank (the 100 test questions are excluded). If the question doesn't sit right against those comps, Vera looks wider at neighboring skills. She then confirms Sol's domain/skill or reassigns them.

For grid-in math questions (no choices), check 2 becomes: the answer Sol gave is the unique correct value (equivalent forms count as the same value).

## Disputes

If Vera disagrees with Sol on the answer, or on domain/skill, Sol gets one response — its reason, in its own words. Vera then rules. Vera's ruling stands; Sol's reason is recorded alongside it either way. All of this is transcribed: Vera's checks, the comps she pulled, any dispute, and the ruling are data.

## What Vera passes on

- The verified answer (or Vera's corrected answer, flagged).
- The verified domain and skill.
- The comps she pulled.
- Her notes: anything she disputed, anything odd about the question (a defensible "wrong" choice, a question that sits between skills).
- Token counts for her own run.

## What Vera is told

Her job as above, and the reason she exists: everything downstream trusts the answer and the domain/skill. If those are wrong, the comps mislead and the rating is built on sand. The fresh baseline's answers were 96.6% right, its domains 97.6%, its skills 93.3% — good, not perfect, and the misses concentrate exactly where a checker earns her keep.
