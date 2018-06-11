# **Termnet** Documentation
Termnets are networks of terms that represent the relationship between those terms in a corpus.
This tool 

When talking about **Termnet**, we commonly use the following notation interchangably:

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
#### Usage
Click the buttons to invoke the respective action.

#### Details
* *Release*: Allow the nodes to move around freely, based off the underlying graph-physics.
* *Lock*: Prohibt the nodes from moving freely, locking them into their current positions.
* *Reset*: Reload the termnet from scratch, clearing any affects of searching, amplifications/dampifications, etc.
This has the same affect as refreshing the page, or loading from a session.

### Neighbourhood
#### Usage
Type the term to focus the graph on into the text-box and press the enter key.
You may press enter on the text-box when empty to clear the previous neighbourhood.

#### Details
A *Neighbourhood* will narrow down the set of nodes visible in the graph.
A more detailed update to the documentation will review precisely how this occurs, suffice to say for now it restricts the graph to only important neighbours of the selected term.

### Search
#### Usage
Type the term to search on into the text-box and press the enter key.
Searching for terms will populate the *Search History* list in the order they are searched.
This history cannot be changed, except by *Reseting* the graph.

#### Details
*Search* tells the **Termnet** that the learner is interested in a term, and should therefore put more importance on it.
Ultimately, this affects the weights $$w_n$$ for all the terms $$N$$ in the graph.

Depending on the kind of graph metric selected (forthcoming), applying search will update the node weights according the following formula:

$$w_n^{t+1} = w_n^t + M_n$$

Where $$M_n$$ is the value of the graph metric for the node $$n$$.
After the new weights at time step $$t+1$$ are calculated, the entire set of weights in the graph are scaled linearly to sum to 1.

$$scaled(w_n) = \dfrac{w_n}{\Sigma_{n \in N} w_n}$$

### Size
#### Usage
Drag the range dial to the left for smaller nodes and to the right for larger nodes.

### Amplify/Dampify
#### Usage
Using each of *Amplify*/*Dampify* involves two controls.

1. Formula selection.
2. Applying the affect (amplification/dampification) to a node.

##### Formula selection
Use this control to choose the rate at which the nodes' affect propagates outwards to other nodes.

In the details below, this sets the functions $$F_a$$ and $$F_d$$.

##### Applying the affect to a node
To apply the amplification or dampification affect to a node, type the term into the text-box and press the enter key.
Adding terms will populate the corresponding *Amplifications* and *Dampifications* lists in alphabetical order.
The affect on a term can be removed by clicking the term from the list.

A node cannot exist as both an amplification and a dampification simultaneously.

In the details below, this populates the sets of terms $$A$$ and $$D$$.

#### Details
*Amplify* and *dampify* is a control which will temporarily alter the weights of the nodes in the graph, according to the selected formula.
It is different from *Search* in two ways:

1. It uses different math to affect the weights of the graph.
2. It is reversible and unordered, whereas *Search* will permanently affect the weights of the graph and order does matter.

Amplify/dampify combines the term $$n$$'s previous weight $$w_n$$ with the propagated weights of the amplified and dampified terms to produce a new altered weight $$\hat{w}_n$$.

$$\hat{w}_n = \dfrac{w_n + amplify(n) + dampify(n)}{1 + A + D}$$

$$amplify(n) = \Sigma_{a \in A}F_a(maxDistance(n) - distance(n, a)) * w_a$$

$$dampify(n) = \Sigma_{d \in D}F_d(distance(n, d)) * w_d$$

$$maxDistance(n) = argmax_{m \in N} distance(n, m)$$

Where $$N$$ is all of the terms in the graph and $$A$$ and $$D$$ are all of the amplification and dampification terms, respectively.
$$F_{\{a,d\}}$$ is the selected formula from the amplify $$a$$ or dampify $$d$$  control.
After the altered weights are calculated, they are then re-scaled linearly to sum to 1.

$$scaled(\hat{w}_n) = \dfrac{\hat{w}_n}{\Sigma_{n \in N} \hat{w}_n}$$

### Ignore
#### Usage
Type the term to ignore into the text-box and press the enter key.
Ignoring terms will populate the *Ignores* list in alphabetical order.
The ignore can be removed by clicking the term from the list.

#### Details
*Ignore* is a mechanism to hide terms from the view of the termnet.
Using ignore does not change any of the math behind the other behaviours of the termnet, such as *Search* or *Amplify*/*Dampify*.
