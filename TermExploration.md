### Term Exploration

#### Task

As a learner is exploring a new topic, can we build off their a-priori knowledge to spoon feed them key concepts.
The hypothesis is that these key concepts will help guide them in the knowledge domain, bootstrapping their conceptual knowledge more quickly so they can perform their research effectively.


\* Question: How to evaluate if this process is effective?


#### Process Sketch

1. Learner enters new topic.
2. Presented a list/graph of terms from which they select the most familiar term.
3. Algorithm searches the corpus or corpora for term cooccurrences with the term from #2.
4. Repeat from #2, now with the terms most relevant to the corpus and what is familiar to the learner.
5. At some point, present terms that the learner should familiarize themselves with.
Maybe this happens continuously, or maybe at this point the process terminates.


##### Ideas

* Algorithm could potentially be influenced by hive experience.
For example, if there are three general 'knowledge paths' that other learnes have paved, then learner will likely be guided along one of these paths.
* Learners should have a way to make 'changes in direction'.
So, at one point if they are presented with terms that they know aren't what they are looking for, then they must be able to tell the algorithm this in some way that it can correct its course.
* Presentation at step #2 may be graphical.
* Also at #2, we probably need the learner to both specify a term or terms that they know and that they don't know.
Otherwise, how does step #5 know which terms to give?
* Does step #3 keep in mind its previous invocations, or is it stateless?


##### Possible Search Algorithm

1. Treat all non-stopwords as potential candidate terms.
2. Find their cooccurrence with the provided term(s).
3. Page rank the graph created by these steps.
May also/instead use our recent work on predicting summary terms by graph indices here.
4. Terms which are deemed uninteresting (the learner doesn't want to explore it) may be disconnected from the graph, or weighted negatively/less in some way.
5. Hive influence may similarily come in the form of positive/additional weighting on known focal terms.
This may further be contextual, so that past learnes with included terms A then put focus on terms X, while other past learners with included terms B then instead put focus on terms Y.

