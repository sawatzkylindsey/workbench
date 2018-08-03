
// SessionKey from url hash, or generated if not present.
var sessionKey = window.location.hash == null || window.location.hash == "" ?
    Math.random().toString(36).substring(5) : window.location.hash.substring(1);
var sessioner = null;
var searcher = null;
var focusMetric = null;
var focuserText = null;
var focuserButton = null;
var sizer = null;
var amplifyAffect = null;
var amplifier = null;
var amplifications = null;
var amplifyToggler = null;
var dampifyAffect = null;
var dampifyer = null;
var dampifications = null;
var dampifyToggler = null;
var ignores = null;
var ignoreToggler = null;
var historyList = null;
var svg = null;
var graphMeta = null;
var graphSummary = null;
var simulation = null;
function restartSimulation() {
    simulation = simulation.alphaTarget(0.1)
        .alphaDecay(0.75)
        .velocityDecay(0.75)
        .restart();
}
var size = 1;
var firstDraw = true;
var amplifySet = new Set();
var dampifySet = new Set();
var ignoreSet = new Set();
var color = d3.scaleOrdinal(d3.schemeCategory20);
var MIN_RADIUS = 5;
var MAX_RADIUS = 50;
var width = 1200;
var height = 700;
var side_width = 275;
var middle_width = 650;
var center_x = middle_width / 2.0;
var center_y = height / 2.0;
var pool_radius = height / 2.5;
var inner_pool_radius = pool_radius / 3.0;
var poolColour = "#001e84";
var rightColour = "red";
var leftColour = "blue";
var intersectColour = "magenta";
var barHeight = 16;
var padding = 0.5;
var startY = (height - (2 * pool_radius)) / 2.0;
var endY = startY + (2 * pool_radius);
//var control_width = center_x - pool_radius - 40;
var termCount = null;
var termCooccurrenceMinimum = null;
var termCooccurrenceMaximum = null;
var termCooccurrenceAverage = null;
var termCooccurrenceCutoff = null;
var propertiesToggler = null;
var properties = null;
var includedList = null;
var includedToggler = null;
var included = null;
var excludedList = null;
var excludedToggler = null;
var excluded = null;
var part = null;
var comparer = null;
var partToggler = null;

$(document).ready(function() {
    svg = d3.select("svg");
    svg.attr("width", middle_width + side_width)
        .attr("height", height);

    var pool = svg.append("circle")
        .style("stroke-width", 5)
        .style("stroke", poolColour)
        .style("fill", "white")
        .attrs({
            class: "pool",
            r: pool_radius,
            cx: 0,
            cy: 0,
            transform: "translate(" + center_x + "," + center_y + ")"
            //x: center_x,
            //y: center_y
        });

        if (sessionKey.includes("&")) {
            part = "whole";
            svg.append("path")
                .attr("d", "M0,0 a1,1,0,0,0,0," + inner_pool_radius * 2)
                .style("stroke-width", 1)
                .style("stroke", leftColour)
                .style("fill", "white")
                .attrs({
                    class: "pool-arc",
                    cx: 0,
                    cy: 0,
                    transform: "translate(" + center_x + "," + (center_y - inner_pool_radius) + ")"
                });
            svg.append("path")
                .attr("d", "M0,0 a1,1,0,0,1,0," + inner_pool_radius * 2)
                .style("stroke-width", 1)
                .style("stroke", rightColour)
                .style("fill", "white")
                .attrs({
                    class: "pool-arc",
                    cx: 0,
                    cy: 0,
                    transform: "translate(" + center_x + "," + (center_y - inner_pool_radius) + ")"
                });
            svg.append("line")
                .style("stroke-width", 1)
                .style("stroke", leftColour)
                .attrs({
                    class: "line",
                    x1: center_x - 0.5,
                    x2: center_x - 0.5,
                    y1: center_y - pool_radius + 2.5,
                    y2: center_y - inner_pool_radius
                });
            svg.append("line")
                .style("stroke-width", 1)
                .style("stroke", rightColour)
                .attrs({
                    class: "line",
                    x1: center_x + 0.5,
                    x2: center_x + 0.5,
                    y1: center_y - pool_radius + 2.5,
                    y2: center_y - inner_pool_radius
                });
            svg.append("line")
                .style("stroke-width", 1)
                .style("stroke", leftColour)
                .attrs({
                    class: "line",
                    x1: center_x - 0.5,
                    x2: center_x - 0.5,
                    y1: center_y + pool_radius - 2.5,
                    y2: center_y + inner_pool_radius
                });
            svg.append("line")
                .style("stroke-width", 1)
                .style("stroke", rightColour)
                .attrs({
                    class: "line",
                    x1: center_x + 0.5,
                    x2: center_x + 0.5,
                    y1: center_y + pool_radius - 2.5,
                    y2: center_y + inner_pool_radius
                });
        }

    $("#controlFo").width(side_width);
    $("#controlFo").load("controls.html", function() {
        sessioner = $("#sessioner");
        sessioner.text("Session: " + sessionKey);
        searcher = $("#searcher");
        focuserText = $("#focuserText");
        focuserButton = $("#focuserButton");
        focusMetric = $("#focusMetric");
        focusMetric.val(focusMetric.find(".default").val())
            .change();
        sizer = $("#sizer");
        amplifyAffect = $("#amplifyAffect");
        amplifyAffect.find(".default")
            .prop("checked", true)
            .change();
        amplifier = $("#amplifier");
        amplifications = $("#amplifications");
        amplifyToggler = $("#amplifyToggler");
        dampifyAffect = $("#dampifyAffect");
        dampifyAffect.find(".default")
            .prop("checked", true)
            .change();
        dampifier = $("#dampifier");
        dampifications = $("#dampifications");
        dampifyToggler = $("#dampifyToggler");
        ignorer = $("#ignorer");
        ignores = $("#ignores");
        ignoreToggler = $("#ignoreToggler");
        historyList = $("#historyList");
        comparer = $("#comparer");
        partToggler = $("#partToggler");

        if (!sessionKey.includes("&")) {
            comparer.style("display", "none");
        }
    });
    var metaFo = svg.append("foreignObject")
        .attr("transform", "translate(" + 0 + "," + 10 + ")")
        //.attr("transform", "translate(" + (center_x - pool_radius) + "," + 15 + ")")
        .attr("width", middle_width)
        .attr("height", ((height - (pool_radius * 2))/ 2) - 20);
    graphMeta = metaFo.append("xhtml:div")
        .attr("id", "graphMeta")
        .attr("class", "label")
        .style("text-align", "center")
        .text("loading..");
    var summaryFo = svg.append("foreignObject")
        .attr("transform", "translate(" + 0 + "," + (center_y + pool_radius + 10) + ")")
        //.attr("transform", "translate(" + (center_x - pool_radius) + "," + (center_y * 1.85) + ")")
        .attr("width", middle_width)
        .attr("height", ((height - (pool_radius * 2))/ 2) - 20);
    graphSummary = summaryFo.append("xhtml:div")
        .attr("id", "graphSummary")
        .attr("class", "label")
        .style("text-align", "center")
        .text("loading..");
    var propertiesFo = svg.append("foreignObject")
        .attr("transform", "translate(" + middle_width + "," + 10 + ")")
        .attr("width", side_width);
        //.attr("height", height);
    propertiesFo.append("xhtml:div")
        .attr("id", "propertiesFo")
        .attr("width", side_width)
        .text("loading..");
    //$("#propertiesFo").width(side_width);
    $("#propertiesFo").load("properties.html", function() {
        termCount = $("#termCount");
        termCooccurrenceMinimum = $("#termCooccurrenceMinimum");
        termCooccurrenceMaximum = $("#termCooccurrenceMaximum");
        termCooccurrenceAverage = $("#termCooccurrenceAverage");
        termCooccurrenceCutoff = $("#termCooccurrenceCutoff");
        propertiesToggler = $("#propertiesToggler");
        properties = $("#properties");
        includedList = $("#includedList");
        includedToggler = $("#includedToggler");
        excludedList = $("#excludedList");
        excludedToggler = $("#excludedToggler");
        //svgRight = d3.select("svgRight");
        //svgRight.attr("width", side_width)
        //    .attr("height", height);
    //svg.attr("width", svg_width)
    //    .attr("height", height);
        d3.json("properties")
            .header("session-key", sessionKey)
            .post("", function(error, data) {
                termCount.text("" + data.total_terms);
                termCooccurrenceMinimum.text("" + data.minimum_cooccurrence_count);
                termCooccurrenceMaximum.text("" + data.maximum_cooccurrence_count);
                termCooccurrenceAverage.text(("" + data.average_cooccurrence_count).substring(0, 4));
                termCooccurrenceCutoff.text("" + data.cutoff_cooccurrence_count);
                included = Array.from(data.included);
                included.sort();
                included.forEach(function(item) {
                    includedList.append("<span style='font-size: 8pt;'>&bull; " + item + "</span></br>");
                });
                excluded = Array.from(data.excluded);
                excluded.sort();
                excluded.forEach(function(item) {
                    excludedList.append("<span style='font-size: 8pt;'>&bull; " + item + "</span></br>");
                });
            });
    });

    simulation = d3.forceSimulation()
        .force("link", d3.forceLink()
            .distance(function(link) { return link.distance; })
            .strength(0.6)
            .id(function(node) { return node.name; })
        )
        .force("collide", d3.forceCollide(function (d) {
            return node_radius(ranking(d.ranks)) * 1.8;
        }))
        .force("charge", d3.forceManyBody()
            .strength(-200)
            .distanceMin(10)
            .distanceMax(pool_radius * 1.5)
        )
        .force("x", d3.forceX(center_x).strength(0.2))
        .force("y", d3.forceY(center_y).strength(0.2));

    console.log("initial reset");
    reset(null);

    var drag_start_x = null;
    var drag_start_y = null;
});
function search(event) {
    if (event.keyCode == 13) {
        var termname = searcher.val();
        searcher.val("");
        console.log("term: " + termname);
        d3.json("search")
            .header("session-key", sessionKey)
            .post("term=" + termname, function(error, data) { draw(data); });
    }
}
function focusAction(event) {
    var termname = null;

    if (event.type == "keydown") {
        if (event.keyCode == 13) {
            termname = focuserText.val();
            focuserText.val("");
        }
    }

    if (event.type == "click" || termname != null) {
        console.log("focus term: " + termname);
        var params = termname == null ? "" : "term=" + termname;
        d3.json("focus")
            .header("session-key", sessionKey)
            .post(params, function(error, data) {
                if (error != null) {
                    // TODO
                } else {
                    draw(data);
                    var prefix = focusMetric.find(":selected").html() + (termname == null ? "" : ": ");
                    var item = termname == null ? "" : termname;
                    historyList.append("<span style='font-size: 11pt;'>&bull; " + prefix + "<span style='color: green'>" + item + "</span></span></br>");
                }
            });
    }
}
function release(event) {
    svg.selectAll(".node")
        .each(function(d) {
            var pyth = pythagoras(d.x, d.y);

            if (pyth.hypotenuse <= pool_radius + 1) {
                d.fx = null;
                d.fy = null;
                d.drag = false;
                //unstick(d);
            }
        });
}
function lock(event) {
    svg.selectAll(".node")
        .each(function(d) {
            var pyth = pythagoras(d.x, d.y);

            if (pyth.hypotenuse <= pool_radius + 1) {
                d.fx = d.x;
                d.fy = d.y;
                d.drag = true;
            }
        });
}
function reset(event) {
    d3.json("reset")
        .header("session-key", sessionKey)
        .post("");
    amplifySet = new Set();
    dampifySet = new Set();
    ignoreSet = new Set();
    updateAmplifications(null);
    updateDampifications(null);
    updateIgnores(null);
    if (historyList != null) {
        historyList.empty();
    }
    firstDraw = true;
    d3.json("search")
        .header("session-key", sessionKey)
        .post("", function(error, data) {
            if (error == null) {
                draw(data);
            } else {
                alert(error.target.statusText + "\nLets start again..");
                window.location.replace("index.html");
            }
        });
}
var BIASED = ["BPR", "IBPR"];
function focusConfigure(event) {
    if (BIASED.indexOf(event.target.value) >= 0) {
        focuserText.css("display", "block");
        focuserButton.css("display", "none");
    } else {
        focuserText.css("display", "none");
        focuserButton.css("display", "block");
    }

    d3.json("focus/configure")
        .header("session-key", sessionKey)
        .post("mode=" + event.target.value, function(error, data) {
            // Don't need to redo anything.
        });
}
function amplifyConfigure(event) {
    d3.json("influence/configure")
        .header("session-key", sessionKey)
        .post("mode=" + event.target.value + "&polarity=positive", function(error, data) {
            if (!event.isTrigger) {
                draw(data);
            }
        });
}
function dampifyConfigure(event) {
    d3.json("influence/configure")
        .header("session-key", sessionKey)
        .post("mode=" + event.target.value + "&polarity=negative", function(error, data) {
            if (!event.isTrigger) {
                draw(data);
            }
        });
}
function amplifyAdd(event) {
    if (event.keyCode == 13) {
        let termname = amplifier.val();
        amplifier.val("");
        dampifySet.delete(termname);
        updateDampifications(termname);
        d3.json("influence")
            .header("session-key", sessionKey)
            .post("polarity=positive&term=" + termname + "&mode=add", function(error, data) {
                if (error == null) {
                    draw(data);
                    amplifySet.add(termname);
                    updateAmplifications(termname);
                }
            });
    }
}
function dampifyAdd(event) {
    if (event.keyCode == 13) {
        let termname = dampifier.val();
        dampifier.val("");
        amplifySet.delete(termname);
        updateAmplifications(termname);
        d3.json("influence")
            .header("session-key", sessionKey)
            .post("polarity=negative&term=" + termname + "&mode=add", function(error, data) {
                if (error == null) {
                    draw(data);
                    dampifySet.add(termname);
                    updateDampifications(termname);
                }
            });
    }
}
function ignoreAdd(event) {
    if (event.keyCode == 13) {
        let termname = ignorer.val();
        ignorer.val("");
        d3.json("ignore")
            .header("session-key", sessionKey)
            .post("term=" + termname + "&mode=add", function(error, data) {
                if (error == null) {
                    draw(data);
                    ignoreSet.add(termname);
                    updateIgnores(termname);
                }
            });
    }
}
function amplifyRemove(event) {
    var termname = event.target.innerText.substring(2, event.target.innerText.length);
    d3.json("influence")
        .header("session-key", sessionKey)
        .post("polarity=positive&term=" + termname + "&mode=remove", function(error, data) {
            draw(data);
            amplifySet.delete(termname);
            updateAmplifications(termname);
        });
}
function dampifyRemove(event) {
    var termname = event.target.innerText.substring(2, event.target.innerText.length);
    d3.json("influence")
        .header("session-key", sessionKey)
        .post("polarity=negative&term=" + termname + "&mode=remove", function(error, data) {
            draw(data);
            dampifySet.delete(termname);
            updateDampifications(termname);
        });
}
function ignoreRemove(event) {
    var termname = event.target.innerText.substring(2, event.target.innerText.length);
    updateIgnores(termname);
    d3.json("ignore")
        .header("session-key", sessionKey)
        .post("term=" + termname + "&mode=remove", function(error, data) {
            draw(data);
            ignoreSet.delete(termname);
            updateIgnores(termname);
        });
}
function updateAmplifications(termname) {
    if (amplifications != null) {
        amplifications.empty();
        var sortedAmplifySet = Array.from(amplifySet);
        sortedAmplifySet.sort();
        sortedAmplifySet.forEach(function(amplify) {
            amplifications.append("<span class='clickable' onclick='amplifyRemove(event)' style='font-size: 11pt;'>&bull; " + amplify + "</span></br>");
        });
        if (amplifyToggler.val() != "Hide") {
            var suffix = amplifySet.size == 0 ? "" : " (" + amplifySet.size + ")";
            amplifyToggler.val("Show" + suffix);
        }
    }
}
function updateDampifications(termname) {
    if (dampifications != null) {
        dampifications.empty();
        var sortedDampifySet = Array.from(dampifySet);
        sortedDampifySet.sort();
        sortedDampifySet.forEach(function(negation) {
            dampifications.append("<span class='clickable' onclick='dampifyRemove(event)' style='font-size: 11pt;'>&bull; " + negation + "</span></br>");
        });
        if (dampifyToggler.val() != "Hide") {
            var suffix = dampifySet.size == 0 ? "" : " (" + dampifySet.size + ")";
            dampifyToggler.val("Show" + suffix);
        }
    }
}
function togglePart(event) {
    if (partToggler.val() == "Whole") {
        part = "left";
        partToggler.val("Left");
    }
    else if (partToggler.val() == "Left") {
        part = "right";
        partToggler.val("Right");
    }
    else {
        part = "whole";
        partToggler.val("Whole");
    }
    drawBars();
}
function toggleAmplifications(event) {
    if (amplifyToggler.val() == "Hide") {
        var suffix = amplifySet.size == 0 ? "" : " (" + amplifySet.size + ")";
        amplifyToggler.val("Show" + suffix);
        amplifications.parent().css("display", "none");
    } else {
        amplifyToggler.val("Hide");
        amplifications.parent().css("display", "block");
    }
}
function toggleDampifications(event) {
    if (dampifyToggler.val() == "Hide") {
        var suffix = dampifySet.size == 0 ? "" : " (" + dampifySet.size + ")";
        dampifyToggler.val("Show" + suffix);
        dampifications.parent().css("display", "none");
    } else {
        dampifyToggler.val("Hide");
        dampifications.parent().css("display", "block");
    }
}
function updateIgnores(termname) {
    if (ignores != null) {
        ignores.empty();
        var sortedIgnoreSet = Array.from(ignoreSet);
        sortedIgnoreSet.sort();
        sortedIgnoreSet.forEach(function(ignore) {
            ignores.append("<span class='clickable' onclick='ignoreRemove(event)' style='font-size: 11pt;'>&bull; " + ignore + "</span></br>");
        });
        if (ignoreToggler.val() != "Hide") {
            var suffix = ignoreSet.size == 0 ? "" : " (" + ignoreSet.size + ")";
            ignoreToggler.val("Show" + suffix);
        }
    }
}
function toggleIgnores(event) {
    if (ignoreToggler.val() == "Hide") {
        var suffix = ignoreSet.size == 0 ? "" : " (" + ignoreSet.size + ")";
        ignoreToggler.val("Show" + suffix);
        ignores.parent().css("display", "none");
    } else {
        ignoreToggler.val("Hide");
        ignores.parent().css("display", "block");
    }
}
function toggleProperties(event) {
    if (propertiesToggler.val() == "Hide") {
        propertiesToggler.val("Show");
        properties.css("display", "none");
        includedToggler.css("display", "none");
        excludedToggler.css("display", "none");
        svg.selectAll(".bar")
            .style("opacity", 1.0);
        svg.selectAll(".barLabel")
            .style("opacity", 1.0);
    } else {
        propertiesToggler.val("Hide");
        properties.css("display", "block");
        includedToggler.css("display", "block");
        excludedToggler.css("display", "block");
        svg.selectAll(".bar")
            .style("opacity", 0.2);
        svg.selectAll(".barLabel")
            .style("opacity", 0.2);
    }
}
function toggleIncluded(event) {
    if (includedToggler.val() == "Hide Included") {
        var suffix = included.length == 0 ? "" : " (" + included.length + ")";
        includedToggler.val("Show Included" + suffix);
        includedList.parent().css("display", "none");
    } else {
        includedToggler.val("Hide Included");
        includedList.parent().css("display", "block");
    }
}
function toggleExcluded(event) {
    if (excludedToggler.val() == "Hide Excluded") {
        var suffix = excluded.length == 0 ? "" : " (" + excluded.length + ")";
        excludedToggler.val("Show Excluded" + suffix);
        excludedList.parent().css("display", "none");
    } else {
        excludedToggler.val("Hide Excluded");
        excludedList.parent().css("display", "block");
    }
}
function node_radius(rank) {
    return Math.min(Math.max(rank * size, MIN_RADIUS), MAX_RADIUS);
}
function resize(event) {
    size = parseInt(sizer.val());
    restartSimulation();        // Make sure the simulation keeps going, otherwise sometimes the resizer gets "stuck".
}
function grouping(groups) {
    if (part == null) {
        return null;
    }

    if (groups.length == 2) {
        return "intersect";
    }
    else if (groups.length == 1 && groups[0] == "left") {
        return "left";
    }
    else if (groups.length == 1 && groups[0] == "right") {
        return "right";
    }
    else {
        assert(false);
    }
}
function ranking(ranks) {
    return Object.values(ranks).reduce((a,b) => a + b);
}
function part_ranking(ranks) {
    if (part == null || part == "whole") {
        return ranking(ranks);
    }
    else {
        return ranks[part];
    }
}
function part_ranking_a(ranks) {
    if (part == "whole" || part == "left") {
        return ranks["left"];
    }
    else {
        return ranks["right"];
    }
}
function part_ranking_b(ranks) {
    if (part == "whole" || part == "left") {
        return ranks["right"];
    }
    else {
        return ranks["left"];
    }
}
var theGraph = null;
function draw(graph) {
    console.log(graph);
    theGraph = graph;
    var previousPositions = {};

    if (!firstDraw) {
        svg.selectAll(".node")
            .each(function(n) {
                previousPositions[n.name] = {x: n.x, y: n.y, drag: n.drag};
            });
        graph.nodes = graph.nodes.map(function(n) {
            if (n.name in previousPositions) {
                n.drag = previousPositions[n.name].drag;

                if (n.drag) {
                    n.fx = previousPositions[n.name].x;
                    n.fy = previousPositions[n.name].y;
                }
                else {
                    n.x = previousPositions[n.name].x;
                    n.y = previousPositions[n.name].y;
                }
            }
            return n;
        });
        console.log(graph);
    }

    firstDraw = false;
    svg.selectAll("g").remove();
    //svgRight.selectAll("g").remove();
    graphMeta.html("<span>Nodes: " + graph.size + "</span></br><span>Selection: " + graph.selection + "</span>");
    graphSummary.text(graph.summary);

    var link = svg.append("g")
        .attr("class", "links")
        .selectAll("links")
        .data(graph.links, function (links) {
            return links;
        })
        .enter()
            .append("line")
            .attr("term-source", function(l) { return l.source; })
            .attr("term-target", function(l) { return l.target; })
            .attr("stroke-width", function(l) {
                return l.alpha == 1.0 ? 1.5 : 1.0;
            })
            .style("stroke-dasharray", function(l) {
                if (l.stroke == "full") {
                    return "1, 0";
                }
                else {
                    return "5, 5";
                }
            })
            .style("opacity", function(l) { return l.alpha; })
            .on("mouseover", function(l) {
            });

    var node = svg.append("g")
        .attr("class", "nodes")
        .selectAll("bob")
        .data(graph.nodes)
        .enter()
            .append("circle")
            .attr("class", "node")
            .attr("id", function(d) { return "node-" + d.name; })
            .attr("fill", function(d) {
                var group = grouping(d.groups);

                if (group == "intersect") {
                    return intersectColour;
                }
                else if (group == "left") {
                    return leftColour;
                }
                else {
                    return rightColour;
                }
            })
            .attr("term", function(d) { return d.name; })
            .attr("r", function(d) { return ranking(d.ranks); })
            .style("opacity", function(d) { return d.alpha; })
            .on("click", unstick)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

    var labels = svg.append("g")
        .attr("class", "labels")
        .selectAll("bobbobobo")
        .data(graph.nodes)
        .enter()
            .append("text")
            .style("pointer-events", "none")
            .attr("class", "label")
            .attr("stroke", "black")
            .attr("term", function(d) { return d.name; })
            .style("opacity", function(d) { return d.alpha / 1.5; })
            .text(function (d) { return d.name; });

    drawBars();

    simulation.nodes(graph.nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(graph.links);

    restartSimulation();

    function ticked() {
        node.attrs(function(d) {
            var coordinates = pool_bound(d);
            d.x = coordinates.x;
            d.y = coordinates.y;
            return {
                cx: coordinates.x,
                cy: coordinates.y,
                r: node_radius(ranking(d.ranks))
            };
        });

        link.attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        labels.attrs(function(d) {
            var radius = node_radius(ranking(d.ranks));
            return {
                x: d.x + 4.5 + radius,
                y: d.y + 4.5
            };
        });
    }
}
function drawBars() {
    svg.selectAll(".bar").remove();
    var maximumBars = Math.floor((endY - startY) / barHeight);
    // Simply makes a copy:   vvvvvvvvv
    var barNodes = theGraph.nodes.slice(0)
        .sort(function(a, b) {
            if (part == null || part == "whole") {
                return ranking(b.ranks) - ranking(a.ranks);
            }
            else if (part == "left") {
                var o = b.ranks["left"] - a.ranks["left"];

                if (o == 0) {
                    return b.ranks["right"] - a.ranks["right"];
                }

                return o;
            }
            else if (part == "right") {
                var o = b.ranks["right"] - a.ranks["right"];

                if (o == 0) {
                    return b.ranks["left"] - a.ranks["left"];
                }

                return o;
            }
        });
    barNodes = barNodes.slice(0, maximumBars);
    var x = d3.scaleLinear()
        .range([0, side_width * 0.9])
        .domain([0, d3.max(barNodes, function(d) { return ranking(d.ranks); })]);
    var y = d3.scaleBand()
        .range([startY, startY + (barNodes.length * barHeight)])
        .domain(barNodes.map(function(d) { return d.name; }));

    if (part == null) {
        var bars = svg.append("g")
            .attr("class", "bars")
            .selectAll("bobboboobobobob")
            .data(barNodes)
            .enter()
                .append("rect")
                .attr("class", "bar")
                .attr("y", function(d) { return y(d.name); })
                .attr("height", barHeight - padding)
                .attr("x", middle_width)
                .attr("width", function(d) { return x(ranking(d.ranks)); })
                .style("fill", leftColour)
                .style("opacity", 1.0);
    } else {
        var orderedBars = svg.append("g")
            .attr("class", "bars")
            .selectAll("bobboboobobobob")
            .data(barNodes)
            .enter()
                .append("rect")
                .attr("class", "bar")
                .attr("y", function(d) { return y(d.name); })
                .attr("height", barHeight - padding)
                .attr("x", middle_width)
                .attr("width", function(d) { return x(part_ranking_a(d.ranks)); })
                .style("fill", function(d) {
                    if (part == "whole" || part == "left") {
                        return leftColour;
                    }
                    else {
                        return rightColour;
                    }
                })
                .style("opacity", 1.0);
        var stackedBars = svg.append("g")
            .attr("class", "bars")
            .selectAll("bobboboobobobob")
            .data(barNodes)
            .enter()
                .append("rect")
                .attr("class", "bar")
                .attr("y", function(d) { return y(d.name); })
                .attr("height", barHeight - padding)
                .attr("x", function(d) { return middle_width + x(part_ranking_a(d.ranks)); })
                .attr("width", function(d) { return x(part_ranking_b(d.ranks)); })
                .style("fill", function(d) {
                    if (part == "whole" || part == "left") {
                        return rightColour;
                    }
                    else {
                        return leftColour;
                    }
                })
                .style("opacity", 1.0);
    }
    var barLabels = svg.append("g")
        .attr("class", "barLabels")
        .selectAll("sdfasfdkajfbobob")
        .data(barNodes)
        .enter()
            .append("text")
            .attr("class", "barLabel")
            .attr("y", function(d) { return y(d.name) + 12; })
            .attr("x", middle_width + 2)
            .style("pointer-events", "none")
            //.attr("class", "label")
            //.attr("stroke", "white")
            .attr("fill", "#999")
            .text(function (d) { return d.name; });

}
function pythagoras(x, y) {
    var distance_x = Math.abs(center_x - x);
    var distance_y = Math.abs(center_y - y);
    return {
        distance_x: distance_x,
        distance_y: distance_y,
        hypotenuse: Math.sqrt(Math.pow(distance_x, 2) + Math.pow(distance_y, 2))
    };
}
function pool_bound(d) {
    if (d.drag) {
        return {x: d.x, y: d.y}
    }

    var pyth = pythagoras(d.x, d.y);
    var group = grouping(d.groups);
    var maximum_radius = pool_radius;
    var minimum_radius = null;
    var left_bound = null;
    var right_bound = null;

    if (group == "intersect") {
        maximum_radius = inner_pool_radius;
    }
    else if (group == "left") {
        minimum_radius = inner_pool_radius;
        right_bound = center_x;
    }
    else if (group == "right") {
        minimum_radius = inner_pool_radius;
        left_bound = center_x;
    }

    if (pyth.hypotenuse > (maximum_radius - 1)) {
        var distance_total = pyth.distance_x + pyth.distance_y;
        var excess = pyth.hypotenuse - (maximum_radius - 1);
        var excess_squared = Math.pow(excess, 2);
        var sign_x = d.x > center_x ? 1 : -1;
        var sign_y = d.y > center_y ? 1 : -1;
        return {
            x: d.x - (sign_x * Math.sqrt(excess_squared * (pyth.distance_x / distance_total))),
            y: d.y - (sign_y * Math.sqrt(excess_squared * (pyth.distance_y / distance_total)))
        };
    }
    else if (minimum_radius != null && pyth.hypotenuse <= (minimum_radius + 1)) {
        var distance_total = pyth.distance_x + pyth.distance_y;
        var excess = (minimum_radius + 1) - pyth.hypotenuse;
        var excess_squared = Math.pow(excess, 2);
        var sign_x = d.x > center_x ? -1 : 1;
        var sign_y = d.y > center_y ? -1 : 1;

        if (left_bound != null) {
            return {
                x: Math.max(d.x - (sign_x * Math.sqrt(excess_squared * (pyth.distance_x / distance_total))), center_x + 1),
                y: d.y - (sign_y * Math.sqrt(excess_squared * (pyth.distance_y / distance_total)))
            };
        } else {
            return {
                x: Math.min(d.x - (sign_x * Math.sqrt(excess_squared * (pyth.distance_x / distance_total))), center_x - 1),
                y: d.y - (sign_y * Math.sqrt(excess_squared * (pyth.distance_y / distance_total)))
            };
        }
    }
    else if (left_bound != null && d.x < (center_x + 1)) {
        return {
            x: center_x + 1,
            y: d.y
        }
    }
    else if (right_bound != null && d.x > (center_x - 1)) {
        return {
            x: center_x - 1,
            y: d.y
        }
    }
    else {
        return {
            x: d.x,
            y: d.y
        }
    }
}
function dragstarted(d) {
    d.fx = d.x;
    d.fy = d.y;
    d.drag = true;
    drag_start_x = d.x;
    drag_start_y = d.y;
}

function dragged(d) {
    if (d3.event.x > 10 && d3.event.x < (middle_width - 10)) {
        d.fx = d3.event.x;
    }

    if (d3.event.y > 10 && d3.event.y < (height - 10)) {
        d.fy = d3.event.y;
    }
}

function dragended(d) {
    var previous_pyth = pythagoras(drag_start_x, drag_start_y);
    drag_start_x = null;
    drag_start_y = null;
    var pyth = pythagoras(d.x, d.y);

    if (pyth.hypotenuse > pool_radius + 1 && previous_pyth.hypotenuse <= pool_radius + 1) {
        d3.json("highlight")
            .header("session-key", sessionKey)
            .post("term=" + d.name + "&mode=add", function(error, data) {
                draw(data);
            });
    } else if (pyth.hypotenuse <= pool_radius && previous_pyth.hypotenuse > pool_radius) {
        d3.json("highlight")
            .header("session-key", sessionKey)
            .post("term=" + d.name + "&mode=remove", function(error, data) {
                draw(data);
            });
    }
}

function unstick(d) {
    d.fx = null;
    d.fy = null;
    d.drag = false
    var previous_pyth = pythagoras(d.x, d.y);

    if (previous_pyth.hypotenuse > pool_radius + 1) {
        d3.json("highlight")
            .header("session-key", sessionKey)
            .post("term=" + d.name + "&mode=remove", function(error, data) {
                draw(data);
            });
    }
}
