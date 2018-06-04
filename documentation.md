# **Termnet** Documentation
Termnets are networks\* of terms\* that represent the relationship between those terms in a corpus.
This tool 

\*When talking about **Termnet**, we commonly use the following notation interchangably:

* termnet <-> network <-> graph
* term <-> node
* relationship <-> edge <-> link

## Process
The process of using the Termnet tool is illustrated in the following diagram.

<img src='cloud-questions.png'/>

## Loading Termnets

## Kind

## Keep %

## Window


## Manipulating Termnets

### Nodes

### Neighbourhood

### Search


### Size

### +/- Influence
Positive and negative influence is a control which will temporarily alter the weights of the nodes in the graph, according to the selected formula.
It is different from *Search* in two ways:

1. It uses different math to affect the weights of the graph.
2. It is reversable, whereas *Search* will permanently affect the weights of the graph.

To calculate the affect of positive or negative influence, first calculate the minimum distance from the influenced node to the rest of the nodes in the graph (including itself).
For negative influence, use this distance directly as the $$x$$ value to the respective influence formula.
For positive influence, use this distance subtracted from the maximum distance from the influenced term as the $x$ value to the respective influence formula.
In both cases, the result is then averaged across all active influences and added to the term.

$$influence(term = t) = \dfrac{positiveInfluence(term) + negativeInfluence(term)}{count(P) + count(N)}$$
$$positiveInfluence(term = t) = \Sigma_{i \in P}(distance)$$

Where $$P$$ and $$N$$ are all of the positive and negative influences, respectively.
$$M_it$$ is the maximum distance from the influence term $$i$$ to the subject term $$t$$.

### Ignore

