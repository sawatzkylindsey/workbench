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

### Amplify/Dampify
#### Usage
Using each of *Amplify*/*Dampify* involves two controls.

1. Formula selection.
2. Applying the affect (amplification/dampification) to a node.

##### Formula selection
Use this control to choose the rate at which the nodes' affect propagates outwards to other nodes.

In the details below, this sets the functions $$F_a$$ and $$F_d$$.

##### Applying the affect to a node
To apply the amplification or dampification affect to a node, enter the corresponding term into the text-box and press the enter key.
A node cannot exist as both an amplification and a dampification simultaneously.

In the details below, this populates the sets of terms $$A$$ and $$D$$.

#### Details
Amplify and dampify is a control which will temporarily alter the weights of the nodes in the graph, according to the selected formula.
It is different from *Search* in two ways:

1. It uses different math to affect the weights of the graph.
2. It is reversible and unordered, whereas *Search* will permanently affect the weights of the graph and order does matter.

Amplify/dampify combines the term $$n$$'s previous weight $$w_n$$ with the propagated weights of the amplified and dampified terms to produce a new altered weight $$w'_n$$.

$$w'_n = \dfrac{w_n + amplify(n) + dampify(n)}{1 + A + D}$$

$$amplify(n) = \Sigma_{a \in A}F_a(maxDistance(n) - distance(n, a)) * w_a$$

$$dampify(n) = \Sigma_{d \in D}F_d(distance(n, d)) * w_d$$

$$maxDistance(n) = arg\,max_{m \in N} distance(n, m)$$

Where $$N$$ is all of the terms in the graph and $$A$$ and $$D$$ are all of the amplification and dampification terms, respectively.
$$F_{\{a,d\}}$$ is the selected formula from the amplify $$a$$ or dampify $$d$$  control.

### Ignore


