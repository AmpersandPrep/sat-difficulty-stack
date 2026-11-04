# Demo video script (tentative, Nov 4, 2026)

Live test drive: Lydia starts Val on two questions on screen, talks while they run, and shows the results when they land. The two questions are a College Board Medium and a College Board Hard that the fresh-model baseline rated wrong; in timed rehearsal runs Val rated both correctly (Medium in 79.3s, Hard in 82.5s).

---

Hi there, judges! I'm Lydia Terry, I run a test prep company called Ampersand Prep. Quick note on what's mine from before and what's new: the Cognitive Agency Approach, my access to the College Board question bank, and my earlier difficulty ratings from other models all predate this week. The four-agent stack and the fresh-model baseline over the full bank were built during the hackathon.

Let's see if this works in real time!

I have a medium and a hard question that a native Muse agent originally got wrong in its assessment. It can usually take a bit to analyze, so I want to get that started now.

So, the problem that I mainly see is that when AI can solve a problem, it therefore thinks the problem is easy to solve. It doesn't account for things like dense language, baited heuristics, stuff the SAT is notorious for. AI doesn't get confused when the question mentions the radius 5 times then asks for the diameter, or when the passage is asking about something Abraham Lincoln said when he was a Senator about the problem with abolitionists.

17-year-olds do. We all do, honestly.

So, I made a stack to try to capture this. We have Sol, a solver, and Vera, a checker, pretty straightforward. But then Snap scrambles the words, numbers, and answers and surmises the topic and potential heuristics a student might encounter. Then we take reports from all of the agents and have Val, the final agent, grade the difficulty considering all of the above.

That's what we are doing now.

Oh good, Val's done.

And there we go. She correctly identified the medium as medium and the hard as hard.

In my world, this is going to help me immensely create quality practice questions for my students and clients. Beyond that, being able to predict the difficulty students encounter will create better ed tech applications, including tutors, apps, worksheets, etc.
