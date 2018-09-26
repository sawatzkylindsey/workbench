Termnet Search Tool Prototype
-----------------------------


### Assumptions/Premise
The premise of this tool is to help students explore the so called *XYZ 220 Data*.
In other words, given a set of roughly 220 short scientific articles, select some subset of roughly 5 articles to write an XYZ paper about.
The paper should draw from the knowledge and connections of ideas from the selected subset of articles.

Since there are many articles to search through, we want to study the effectiveness of using a termnet to help dig through the articles.
This tool is designed to help students answer the question "Which subset of ~5 articles should I select?".

This design documents aims to show a high level sketch of a proposal for a tool to help with this question.
It purposefully stays away from describing any mathematical/computational aspects of the tool.
These details can be decided upon after agreement on the assumptions and general tool design.

Although we may want to answer other questions around this dataset, those should be reserved for a separate tool/design.
Deciding on a different question or rephrasing the currently assumed question are acceptable changes to this document, however they may in turn change the proposed design.


#### Widgets
* Search
* History
* Termnet
* Articles

#### Images
* [Tool Single View](./ToolSingleView.pdf)
* [Supplementary Explanations](./SupplementaryExplanations.pdf)

### Tool Single View
This attachment shows a full fledged view of the tool, with all of its its widgets laid out together.
Every widget has different interactions whose operations will be described shortly.

Before landing at the tool, some pre-processing has been done in order to represent the set of articles as as termnet, index terms within articles, etc.
Suffice to say, the tool holds any necessary representations such as:
* term-sentence cooccurrence across all articles
* term-sentence coocurrence within each article
* mapping of which terms exist in which articles
* etc

### Search
**Search** allows the student to place importance or disinterest on terms/phrases, describing their intent and interests.
Terms/phrases may be typed into the `text box` with an optional +/- prefix (by default, searching for a term uses a +).
\+ indicates that the student is interested in the term, whereas - indicates a lack of interest in the term.
A term can only be included in the search once at a time (a term cannot be searched as both + and -).

As term/phrases are typed, the `chicklets` below the text box are updated.
Clicking on a chicklet removes it from the search.

Searching for a term/phrase will affect the ranks of the terms in the termnet, where + terms and their closer relations are given more weight, and - terms and their closer relations are given less weight.
These weights will also affect the ranking of **Articles**, described later.
The entire set of search terms/phrases consistutes the current search, and the order of the terms is irrelevant (searching for +bananas then -apples is no different from searching for -apples then +bananas).

The only way to affect term weights is through the **Search**, although the **Termnet** does provide a shortcut allowing for search terms to be added to the search without typing.
Moreover, the only effect of the **Search** widget is to change the weights of the terms in the termnet.
**Search** has nothing to do with showing or not showing certain terms in the termnet. 

##### Phrases
This document describes a Terment Search Tool which allows for phrasal searches.
A first draft implementation needn't worry about allowing for phrase based searches, and may assume that only known terms are searchable.
At a later point we may describe how unknown-terms or phrases are mapped to known terms.

### History
**History** shows a flat list of all of the previous searches, giving the student some context around their previous searches and how they have arrived at the current search.
As each search is simply a set of +/- terms, these can be displayed quite easily.
Clicking on a `row` in the history will load that set of search terms into the **Search**.

### Termnet
The **Termnet** allows the student to view and explore the terms of the current search.
Terms with a higher rank will appear bigger than those with lower rank, and term cooccurrence is indicated with an edge connecting two cooccurring terms.
The terms of the current search are all placed within the inner most `0` circle, and then terms 1 edge away are located in the `1` circle, terms 2 edges away in the `2` circle, and so on.

As was noted earlier, the **Search** does not show or hide terms in any way, it only affects their rank.
The **Termnet** is where terms actually can actually be shown or hidden.

Clicking within a circle will cause the terms in all other circles to lose focus or completely fade away.
Re-clicking within the same circle will undo this effect.
This is shown in the bottom right diagram of *Supplementary Explanations*.

The K top ranked terms currently in view will always show as more visible than the lower ranked terms.
If a circle has been clicked as described in the previous paragraph, then only terms within that circle will show as more visible.
K can be altered by controlling the `more/less` slider in the top left of the **Termnet**.

The top middle has an element `scope/context`, which will be described more later.
At the onset, this element will not be visible at all.

Finally, hovering over a term in the **Termnet** will show a clickable + and - button.
Clicking on either of these will update the **Search** with that term.
This is shown in the bottom left diagram of *Supplementary Explanations*.

### Articles
**Articles** allows the student to see the articles most relevant to their current search.
The articles are ranked accordingly so that articles containing terms with higher rank are also higher in rank.

Each article is listed with its `title` and with the set of `terms` it contains.
These `terms` are ordered according to their relative importance within the article (which may be different from their global rank according to the current search).
This gives the student a sense of the importance of the terms within the article itself and independent of the learner's search.

The article `row` may be clicked to change the `scope/context` of the **Termnet**.
This will re-populate the **Termnet** with the terms only contained within the article.
For example, if the article *Title 2* is selected, since that articles doesn't contain the term *fruit*, then the termnet will be drawn without *fruit* (even though *fruit* may be one of the search terms).
This is shown in the top diagram of *Supplementary Explanations*.

Otherwise, the **Termnet** display and interactions remain the same as previously described.
Re-clicking the same article will undo the selection, repopulating the **Termnet** with all the terms and removing the `scope/context`.
