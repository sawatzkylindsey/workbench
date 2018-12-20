# **Termnet** Documentation
Termnets are networks of terms that represent the relationship between those terms in a corpus.

When talking about **Termnet**, we commonly use the following notation interchangably:

* termnet, network, graph
* term, node
* relationship, edge, link

## Process
1. Loading Termnets.
2. Studying Termnets.

## Loading Termnets
We must always begin by producing a termnet from some input corpus and set of terms.
There are several formats that termnets can be loaded from, as well as several settings which will affect how the corpus is interpreted to generate the final termnet.

### Kind
How to generate the termnet.

* *Preset*: Use some curated input data.
* *Custom*: Generate from custom input data.
* *Session*: Reload a past termnet (these may disappear after some time).
* *Compare*: Compare the similarities/differences between two sessions.

### Format
The format of input to generate a terment from.

#### Content Terms
The most common format, whereby the input is two structured documents.

1. The corpus (content).
2. The terms to find.

The terms allow for the equivalence operator `<=`.
Example:

    Jurrasic.
    Jurrasic Park.
    Dinosaur <= Triceratops.
    Dinosaur <= Albertosaurus.

#### Glossary Definitions
TODO

#### Wikipedia Articles List
TODO

### Keep %
How much percentage of the term cooccurrences to keep.
The larger the percent, the more terms and term connections.

### Separator Kind
The type of cooccurrence separator.

* Sentence: Cooccurrences are found inside of sentences, which are separated by a period (`.`).
* Paragraph: Cooccurrences are found inside of a paragraph, which are separated by two returns.

### Window
The window of sentence/paragraphs to find coccurrences within.
`1` is typical, but using larger values will mean that cooccurrences can be found across sentences.
For example, with a window=`2` the following sentences will generate the cooccurrences:

* `chocolate` and `pretzels`
* `pretzels` and `coffee`.

> I eat chocolate.  I eat pretzels.  I drink coffee.

Notice how a cooccurrence between `chocolate` and `coffee` won't be found - this is because these terms are greater than `2` sentences apart.

## Studying Termnets
The termnet is divided into three untitled vertical sections.
From left to right these are operations, termnet, and properties/weight-bar-chart.

The middle termnet section is where the terms and their relations (cooccurrences) are shown.
Only the top 10 weighted terms are shown as full colour, except for when a term is dragged out of the circle then its direct connections are shown.
When all the terms have the same weight, they are all drawn in full colour.

Above the termnet circle is the *Nodes:* and *Selection:* which show how many nodes are currently being displayed and how many are displayed in full colour, respectively.

The right poperties/weight-bar-chart section shows the weights of the top terms as a horizontal bar chart.
When the weights are changed this chart will update accordingly.

### Properties
Show or hide the properties in the right-most vertical section.
Showing the properties will fade out the weight-bar-chart.

### Nodes
* *Release*: Allow the nodes to move around freely, based off the underlying graph-physics.
* *Lock*: Prohibt the nodes from moving freely, locking them into their current positions.
* *Reset*: Reload the termnet from scratch, clearing any affects of searching, focusing, amplifications/dampifications, etc.
This has the same affect as refreshing the page, or loading from a session.
* *Drag*: This element is not a button, but placed here to draw attention to the fact that nodes may be dragged.
Dragging a node will lock it in-place (like a local *Lock*).
Additionally, a node that is dragged out the circle will become highlighted.

### Search
Narrow down the terms displayed to some subset closest to the specified search term.
Only nodes 2-3 edges away will remain in the termnet.

### Focus
Alter the underlying weights of the nodes in the termnet.
Some metrics are global, and other are term specific (aka biased).
If a global metric has been selected, a button *Apply* will appear which can be clicked to apply the metric.
If a biased metric has been selected, a text-box will appear.
Type the bias term into the text-box and press the enter key to apply the biased metric.

* *PR*: [PageRank](https://en.wikipedia.org/wiki/PageRank): A metric which ranks nodes based off the rank of their ancestors.
Generally speaking, nodes that are referred to by many other nodes get a high rank, while nodes which are barely referred to get a low rank.
PageRank is a form of [Eigenvector Centrality](https://en.wikipedia.org/wiki/Eigenvector_centrality).
* *PR-1*: Inverse PageRage: The inverse of PageRank, calculated by taking the ranks from PageRank and inverting them (large in PR becomes small in PR-1, small in PR becomes large in PR-1).
* *BPR*: Biased PageRank: The PageRank metric, but biased towards the terms of the graph.
This metric is different for every term.
* *BPR-1*: Inverse Biased PageRank: The inverse of Biased PageRank, calculated by taking the ranks from Biased PageRank and inverting them (large in BPR becomes small in BPR-1, small in BPR becomes large in BPR-1).
* *CC*: [Clustering Coefficient](https://en.wikipedia.org/wiki/Clustering_coefficient): A metric which ranks nodes based off how closely they are clustered together.
Generally speaking, this metric can stand in for how much nodes are gateways into clusters vs. how much nodes are central to a cluster of nodes.
* *CC-1*: Inverse Clustering Coefficient: The inverse of Clustering Coefficient, calculated by taking the ranks from Clustering Coefficient and inverting them (large in CC becomes small in CC-1, small in CC becomes large in CC-1).

Focusing for terms will populate the *Focus History* list in the order they are selected.
This history cannot be changed, except by *Reseting* the graph.

### Size
Drag the range dial to the left for smaller nodes and to the right for larger nodes.

### Amplify/Dampify
Temporarily alter the weights of the nodes in the graph, according to the selected formula.
It is different from *Focus* in two ways:

1. It uses different math to affect the weights of the graph.
2. It is reversible and unordered, whereas *Focus* will permanently affect the weights of the graph and order does matter.

### Ignore
Hide terms from the view of the termnet.
Using ignore does not change any of the math behind the other behaviours of the termnet, such as *Focus* or *Amplify*/*Dampify*.

