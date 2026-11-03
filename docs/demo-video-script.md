# Demo video script (Lydia Terry, dictated Nov 3, 2026)

Hi, my name is Lydia Terry. I'm the owner of Ampersand Prep, an SAT and ACT tutoring company, and the designer of the Cognitive Agency Approach, which is a novel and rather impactful approach to test prep tutoring. What existed before today is essentially knowledge of the problem I am trying to address with this project.


The SAT is a standardized test typically taken by high school students all over the world as part of their college application process for English-speaking college and university programs.

Over the past 10 years or so, its value in that role, in that process, has been debated, politicized, monetized, and extensively studied. During Covid, many universities changed their position on whether they require, value, or consider the SAT, which gave researchers quite a bit to work with. What they found was that the SAT was a better predictor of freshman grades and graduation rates, "college readiness," than grade point average.

Also, over the past while, AI has been used to help students, parents, educators, and ed tech companies in test prep, to varying degrees of success, in my opinion.


In my world specifically, AI is being used as a psychometrician to evaluate the difficulty of third-party questions.

So although College Board, the nonprofit that owns and administers the SAT, has an extensive question bank of practice questions, parents, students, and educators want more.

As an expert, I am asked to develop practice questions. I recently wrote approximately 200 SAT questions. While the various AI models could answer the question, explain the process, why a right answer is right and why the wrong answers are wrong, what they could not do is determine difficulty.

Difficulty on the SAT is a very important metric because the test is adaptive. Get questions right and the test gets harder. Get questions wrong and the test gets easier.


I gave ChatGPT, Claude, and Grok 610 hard questions. All hard. ChatGPT was correct 40 percent of the time and called 18 percent Easy. Claude was correct 13 percent and called a third Easy. Grok gave up after 58 questions and just said Medium all the way down.


For my hackathon project, I set out to build an agent stack that could do better. I had a fresh Muse agent, what a 17-year-old might use to ask for help, determine the difficulty ratings of the complete known College Board question bank. While it got 96.6 percent of the answers right, it matched College Board's difficulty ratings only 50.8 percent of the time, a kappa of 0.256, barely better than chance agreement.


The problem is, an SAT question is considered difficult the more students miss it. So, a math question that has several steps 11th graders do every day isn't hard, but a question that asks about something Abraham Lincoln said as a senator criticizing abolitionists is.

I systematically tested various methods and gave different jobs to different agents to work out what makes a question hard. Some worked, some did not. After trial and error, the stack that did the best included a solver, a separate checker, a word cloud meant to help AI anticipate the human tendency to surmise a gist, and a list of baitable heuristics.

I ended up with a stack that was able to predict difficulty at this accuracy.

Honestly, this was much harder than I expected it to be. But I am excited by the result. This is bigger than the SAT, it's just that the SAT offered a question bank psychometrically balanced to a student's experience. I used that to create a stack that can predict what students find difficult.

The implications for AI Powered Ed Tech are clear to me. Better AI tutors, better predictive models, better AI audits of ED tech, and more.

Thank you to Muse for this opportunity!
