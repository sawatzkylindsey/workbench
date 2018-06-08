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

##### Applying the affect to a node
To apply the amplification or dampification affect to a node, enter the corresponding term into the textbox and press the enter key.

#### Details
Amplify and dampify is a control which will temporarily alter the weights of the nodes in the graph, according to the selected formula.
It is different from *Search* in two ways:

1. It uses different math to affect the weights of the graph.
2. It is reversible, whereas *Search* will permanently affect the weights of the graph.

To calculate the affect of the amplification/dampification, first calculate the minimum distance from the selected node to the rest of the nodes in the graph (including itself).
For dampification, use this distance directly as the $x$ value to the respective formula.
For amplification, use this distance subtracted from the maximum distance from the influenced term as the $x$ value to the respective formula.
In both cases, the result is then averaged across all active amplifications/dampifications and added to the term.

$weight(term = t) = \dfrac{base(t) + amplify(t) + dampify(t)}{1 + A + D}$

$amplify(term = t) = \Sigma_{a \in A}F_a(maxDistance(t) - distance(t, a)) * base(a)$

$dampify(term = t) = \Sigma_{d \in D}F_d(distance(t, d)) * base(d)$

$maxDistance(term = t) = arg\,max_{i \in T} distance(t, i)$

Where $T$ is all of the terms and $A, D$ are all of the amplifications and dampifications, respectively.
$F$ is the selected formula from the amplify or dampify control.
Finally, $base$ is the current weight of the term as affected by searching.

### Ignore


