
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
var svg_width = 650;
var center_x = svg_width / 2.0;
var center_y = height / 2.0;
var pool_radius = height / 2.5;
//var control_width = center_x - pool_radius - 40;
var termCount = null;
var termCooccurrenceMinimum = null;
var termCooccurrenceMaximum = null;
var termCooccurrenceAverage = null;
var termCooccurrenceCutoff = null;
var includedList = null;
var includedToggler = null;
var included = null;
var excludedList = null;
var excludedToggler = null;
var excluded = null;

$(document).ready(function() {
    svg = d3.select("svg");
    svg.attr("width", svg_width)
        .attr("height", height);

    var pool = svg.append("circle")
        .style("stroke-width", 5)
        .style("stroke", "#001e84")
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
    });
    var metaFo = svg.append("foreignObject")
        .attr("transform", "translate(" + 0 + "," + 10 + ")")
        //.attr("transform", "translate(" + (center_x - pool_radius) + "," + 15 + ")")
        .attr("width", svg_width)
        .attr("height", ((height - (pool_radius * 2))/ 2) - 20);
    graphMeta = metaFo.append("xhtml:div")
        .attr("id", "graphMeta")
        .attr("class", "labels")
        .style("text-align", "center")
        .text("loading..");
    var summaryFo = svg.append("foreignObject")
        .attr("transform", "translate(" + 0 + "," + (center_y + pool_radius + 10) + ")")
        //.attr("transform", "translate(" + (center_x - pool_radius) + "," + (center_y * 1.85) + ")")
        .attr("width", svg_width)
        .attr("height", ((height - (pool_radius * 2))/ 2) - 20);
    graphSummary = summaryFo.append("xhtml:div")
        .attr("id", "graphSummary")
        .attr("class", "labels")
        .style("text-align", "center")
        .text("loading..");
    /*var propertiesFo = svg.append("foreignObject")
        .attr("id", "propertiesFo")
        .attr("transform", "translate(" + (center_x + pool_radius + 20) + ",10)")
        .attr("width", center_x - pool_radius - 40)
        .attr("height", height - 40);*/
    $("#propertiesFo").width(side_width);
    $("#propertiesFo").load("properties.html", function() {
        termCount = $("#termCount");
        termCooccurrenceMinimum = $("#termCooccurrenceMinimum");
        termCooccurrenceMaximum = $("#termCooccurrenceMaximum");
        termCooccurrenceAverage = $("#termCooccurrenceAverage");
        termCooccurrenceCutoff = $("#termCooccurrenceCutoff");
        includedList = $("#includedList");
        includedToggler = $("#includedToggler");
        excludedList = $("#excludedList");
        excludedToggler = $("#excludedToggler");
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
function toggleIncluded(event) {
    if (includedToggler.val() == "Hide") {
        var suffix = included.length == 0 ? "" : " (" + included.length + ")";
        includedToggler.val("Show" + suffix);
        includedList.parent().css("display", "none");
    } else {
        includedToggler.val("Hide");
        includedList.parent().css("display", "block");
    }
}
function toggleExcluded(event) {
    if (excludedToggler.val() == "Hide") {
        var suffix = excluded.length == 0 ? "" : " (" + excluded.length + ")";
        excludedToggler.val("Show" + suffix);
        excludedList.parent().css("display", "none");
    } else {
        excludedToggler.val("Hide");
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
function draw(graph) {
    console.log(graph);
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
                return d.colour;
            })
            .attr("term", function(d) { return d.name; })
            .attr("r", function(d) { return node_radius(d.rank); })
            .style("opacity", function(d) { return d.alpha; })
            .on("click", unstick)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

    var labels = svg.append("g")
        .attr("class", "label")
        .selectAll("bobbobobo")
        .data(graph.nodes)
        .enter()
            .append("text")
            .style("pointer-events", "none")
            .attr("class", "labels")
            .attr("stroke", "black")
            .attr("term", function(d) { return d.name; })
            .style("opacity", function(d) { return d.alpha / 1.5; })
            .text(function (d) { return d.name; });

    simulation.nodes(graph.nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(graph.links);

    restartSimulation();

    function ticked() {
        node.attrs(function(d) {
            var coordinates = pool_bound(node_radius(d.rank), d.x, d.y, d.drag);
            d.x = coordinates.x;
            d.y = coordinates.y;
            return {
                cx: coordinates.x,
                cy: coordinates.y,
                r: node_radius(d.rank)
            };
        });

        link.attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        labels.attrs(function(d) {
            var radius = node_radius(d.rank);
            return {
                x: d.x + 4.5 + radius,
                y: d.y + 4.5
            };
        });
    }
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
function pool_bound(radius, x, y, ignore) {
    var pyth = pythagoras(x, y);

    if (pyth.hypotenuse > pool_radius && !ignore) {
        var distance_total = pyth.distance_x + pyth.distance_y;
        var excess = pyth.hypotenuse - pool_radius;
        var excess_squared = Math.pow(excess, 2);
        var sign_x = x > center_x ? 1 : -1;
        var sign_y = y > center_y ? 1 : -1;
        return {
            x: x - (sign_x * Math.sqrt(excess_squared * (pyth.distance_x / distance_total))),
            y: y - (sign_y * Math.sqrt(excess_squared * (pyth.distance_y / distance_total)))
        };
    }
    else {
        return {x: x, y: y}
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
    if (d3.event.x > 10 && d3.event.x < (svg_width - 10)) {
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
