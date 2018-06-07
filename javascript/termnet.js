
// SessionKey from url hash, or generated if not present.
var sessionKey = window.location.hash == null || window.location.hash == "" ?
    Math.random().toString(36).substring(5) : window.location.hash.substring(1);
var sessioner = null;
var neighbourhooder = null;
var searcher = null;
var sizer = null;
var positiveInfluencer = null;
var negativeInfluencer = null;
var negater = null;
var ignorer = null;
//var negatedToggler = null;
var negaterList = null;
var negaterToggler = null;
var ignorerList = null;
var ignorerToggler = null;
var historyList = null;
var svg = null;
var graphMeta = null;
var graphSummary = null;
var simulation = null;
var rainbow = new Rainbow();
rainbow.setNumberRange(0, 1.0);
rainbow.setSpectrum("#96afff", "#001e84");
var size = 1;
var firstDraw = true;
var negations = new Set();
var ignores = new Set();
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
    .style("stroke", "black")
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
    neighbourhooder = $("#neighbourhooder");
    searcher = $("#searcher");
    sizer = $("#sizer");
    positiveInfluencer = $("#positiveInfluencer");
    positiveInfluencer.find(".default")
        .prop("checked", true)
        .change();
    negativeInfluencer = $("#negativeInfluencer");
    negativeInfluencer.find(".default")
        .prop("checked", true)
        .change();
    negater = $("#negater");
    negaterList = $("#negaterList");
    negaterToggler = $("#negaterToggler");
    ignorer = $("#ignorer");
    ignorerList = $("#ignorerList");
    ignorerToggler = $("#ignorerToggler");
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
        .distance(80)
        //.strength(0.005)
        .id(function(d) { return d.name; })
    )
    .force("charge", d3.forceManyBody().strength(-100))
    .force("x", d3.forceX(center_x).strength(0.05))
    .force("y", d3.forceY(center_y).strength(0.05));

console.log("initial reset");
reset(null);

var drag_start_x = null;
var drag_start_y = null;
});

function neighbourhood(event) {
    if (event.keyCode == 13) {
        var termname = neighbourhooder.val();
        neighbourhooder.val("");
        console.log("term: " + termname);
        d3.json("neighbourhood")
            .header("session-key", sessionKey)
            .post("term=" + termname, function(error, data) { draw(data); });
    }
}
function search(event) {
    if (event.keyCode == 13) {
        var termname = searcher.val();
        searcher.val("");
        console.log("term: " + termname);
        d3.json("search")
            .header("session-key", sessionKey)
            .post("term=" + termname, function(error, data) {
                if (error != null) {
                    // TODO
                } else {
                    draw(data);
                    historyList.append("<span style='font-size: 11pt;'>&bull; " + termname + "</span></br>");
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
    negations = new Set();
    ignores = new Set();
    updateNegations(null);
    updateIgnores(null);
    firstDraw = true;
    d3.json("neighbourhood")
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
function influenceConfigure(event) {
    console.log(event);
    console.log(event.target.value);
    var polarity = event.target.name == "positive-influence" ? "positive" : "negative";
    d3.json("influence/configure")
        .header("session-key", sessionKey)
        .post("mode=" + event.target.value + "&polarity=" + polarity, function(error, data) {
            if (!event.isTrigger) {
                draw(data);
            }
        });
}
function negateAdd(event) {
    //if (!d3.event.active) {
    //    simulation.alphaTarget(0);
    //}
    if (event.keyCode == 13) {
        let termname = negater.val();
        negater.val("");
        d3.json("influence")
            .header("session-key", sessionKey)
            .post("polarity=negative&term=" + termname + "&mode=add", function(error, data) {
                if (error == null) {
                    draw(data);
                    negations.add(termname);
                    updateNegations(termname);
                }
            });
        //negater.val("");
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
                    ignores.add(termname);
                    updateIgnores(termname);
                }
            });
    }
}
function negateRemove(event) {
    var termname = event.target.innerText.substring(2, event.target.innerText.length);
    d3.json("influence")
        .header("session-key", sessionKey)
        .post("polarity=negative&term=" + termname + "&mode=remove", function(error, data) { 
            draw(data);
            negations.delete(termname);
            updateNegations(termname);
        });
}
function ignoreRemove(event) {
    var termname = event.target.innerText.substring(2, event.target.innerText.length);
    updateIgnores(termname);
    d3.json("ignore")
        .header("session-key", sessionKey)
        .post("term=" + termname + "&mode=remove", function(error, data) {
            draw(data);
            ignores.delete(termname);
            updateIgnores(termname);
        });
}
function updateNegations(termname) {
    if (negaterList != null) {
        negaterList.empty();
        var sortedNegations = Array.from(negations);
        sortedNegations.sort();
        sortedNegations.forEach(function(negation) {
            negaterList.append("<span class='clickable' onclick='negateRemove(event)' style='font-size: 11pt;'>&bull; " + negation + "</span></br>");
        });
        if (negaterToggler.val() != "Hide") {
            var suffix = negations.size == 0 ? "" : " (" + negations.size + ")";
            negaterToggler.val("Show" + suffix);
        }
    }
}
function toggleNegations(event) {
    if (negaterToggler.val() == "Hide") {
        var suffix = negations.size == 0 ? "" : " (" + negations.size + ")";
        negaterToggler.val("Show" + suffix);
        negaterList.parent().css("display", "none");
    } else {
        negaterToggler.val("Hide");
        negaterList.parent().css("display", "block");
    }
}
function updateIgnores(termname) {
    if (ignorerList != null) {
        ignorerList.empty();
        var sortedIgnores = Array.from(ignores);
        sortedIgnores.sort();
        sortedIgnores.forEach(function(ignore) {
            ignorerList.append("<span class='clickable' onclick='ignoreRemove(event)' style='font-size: 11pt;'>&bull; " + ignore + "</span></br>");
        });
        if (ignorerToggler.val() != "Hide") {
            var suffix = ignores.size == 0 ? "" : " (" + ignores.size + ")";
            ignorerToggler.val("Show" + suffix);
        }
    }
}
function toggleIgnores(event) {
    if (ignorerToggler.val() == "Hide") {
        var suffix = ignores.size == 0 ? "" : " (" + ignores.size + ")";
        ignorerToggler.val("Show" + suffix);
        ignorerList.parent().css("display", "none");
    } else {
        ignorerToggler.val("Hide");
        ignorerList.parent().css("display", "block");
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
    simulation.alphaTarget(1);  // Make sure the simulation keeps going, otherwise sometimes the resizer gets "stuck".
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
                n.fx = previousPositions[n.name].x;
                n.fy = previousPositions[n.name].y;
                n.drag = previousPositions[n.name].drag;
            }
            return n;
        });
        console.log(graph);
    }

    firstDraw = false;
    svg.selectAll("g").remove();
    graphMeta.text("Nodes: " + graph.size);
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
            .attr("stroke-width", function(l) { return Math.sqrt(l.value); })
            .style("opacity", function(l) { return l.alpha; } );

    var node = svg.append("g")
        .attr("class", "nodes")
        .selectAll("bob")
        .data(graph.nodes)
        .enter()
            .append("circle")
            .attr("class", "node")
            .attr("id", function(d) { return "node-" + d.name; })
            .attr("fill", function(d) {
                return "#" + rainbow.colourAt(d.coeff);
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

    simulation.alphaTarget(0.5).restart();

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

function xbounded(d) { return Math.max(Math.min(d.x, width - 50), 10); }
function ybounded(d) { return Math.max(Math.min(d.y, height - 10), 10); }

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
    if (!d3.event.active) {
        simulation.alphaTarget(0.3).restart();
    }
    d.fx = d.x;
    d.fy = d.y;
    d.drag = true;
    console.log(d);
    drag_start_x = d.x;
    drag_start_y = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function dragended(d) {
    if (!d3.event.active) {
        simulation.alphaTarget(0);
    }
    console.log(d);
    console.log(d3.event);

    var previous_pyth = pythagoras(drag_start_x, drag_start_y);
    drag_start_x = null;
    drag_start_y = null;
    var pyth = pythagoras(d.x, d.y);

    if (pyth.hypotenuse > pool_radius && previous_pyth.hypotenuse <= pool_radius + 1) {
        d3.json("influence")
            .header("session-key", sessionKey)
            .post("polarity=positive&term=" + d.name + "&mode=add", function(error, data) { draw(data); } );
    } else if (pyth.hypotenuse <= pool_radius && previous_pyth.hypotenuse > pool_radius) {
        d3.json("influence")
            .header("session-key", sessionKey)
            .post("polarity=positive&term=" + d.name + "&mode=remove", function(error, data) { draw(data); } );
    }
}

function unstick(d) {
    d.fx = null;
    d.fy = null;
    d.drag = false
    d3.json("influence")
        .header("session-key", sessionKey)
        .post("polarity=positive&term=" + d.name + "&mode=remove", function(error, data) { draw(data); });
    simulation.alphaTarget(0.1);
}
