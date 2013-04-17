function packages_treemap(chart_id, orderings, default_order) {
    var jq_div = jQuery(chart_id),
        color = d3.scale.category20();
    var key_func = function(d) { return d.key; };
    var value_package_count = function(d) { return d.count; },
        value_flagged_count = function(d) { return d.flagged; },
        value_compressed_size = function(d) { return d.csize; },
        value_installed_size = function(d) { return d.isize; };

    /* tag the function so when we display, we can format filesizes */
    value_package_count.is_size = value_flagged_count.is_size = false;
    value_compressed_size.is_size = value_installed_size.is_size = true;

    var treemap = d3.layout.treemap()
        .size([jq_div.width(), jq_div.height()])
        /*.sticky(true)*/
        .value(value_package_count)
        .sort(function(a, b) { return a.key < b.key; })
        .children(function(d) { return d.data; });

    var cell_html = function(d) {
        if (d.children) {
            return "";
        }
        var valuefunc = treemap.value();
        var value = valuefunc(d);
        if (valuefunc.is_size && value !== undefined) {
            value = format_filesize(value);
        }
        return "<span>" + d.name + ": " + value + "</span>";
    };

    var d3_div = d3.select(jq_div.get(0));

    var prop_px = function(prop, offset) {
        return function(d) {
            var dist = d[prop] + offset;
            if (dist > 0) {
                return dist + "px";
            }
            else {
                return "0px";
            }
        };
    };

    var cell = function() {
        /* the -1 offset comes from the border width we use in the CSS */
        this.style("left", prop_px("x", 0)).style("top", prop_px("y", 0))
            .style("width", prop_px("dx", -1)).style("height", prop_px("dy", -1));
    };

    var fetch_for_ordering = function(order) {
        d3.json(order.url, function(json) {
            var nodes = d3_div.data([json]).selectAll("div")
                .data(treemap.nodes, key_func);
            /* start out new nodes in the center of the picture area */
            var w_center = jq_div.width() / 2,
                h_center = jq_div.height() / 2;
            nodes.enter().append("div")
                .attr("class", "treemap-cell")
                .attr("title", function(d) { return d.name; })
                .style("left", w_center + "px").style("top", h_center + "px")
                .style("width", "0px").style("height", "0px")
                .style("display", function(d) { return d.children ? "none" : null; })
                .html(cell_html);
            nodes.transition().duration(1500)
                .style("background-color", function(d) {
                    return d.children ? null : color(d[order.color_attr]);
                })
                .call(cell);
            nodes.exit().transition().duration(1500).remove();
        });
    };

    /* start the callback for the default order */
    fetch_for_ordering(orderings[default_order]);

    var make_scale_button = function(name, valuefunc) {
        var button_id = chart_id + "-" + name;
        /* upon button click, attach new value function and redraw all boxes
         * accordingly */
        d3.select(button_id).on("click", function() {
            d3_div.selectAll("div")
                .data(treemap.value(valuefunc), key_func)
                .html(cell_html)
                .transition().duration(1500).call(cell);

            /* drop off the '#' sign to convert id to a class prefix */
            d3.selectAll("." + chart_id.substring(1) + "-scaleby")
                .classed("active", false);
            d3.select(button_id).classed("active", true);
        });
    };

    /* each scale button tweaks our value, e.g. net size function */
    make_scale_button("count", value_package_count);
    make_scale_button("flagged", value_flagged_count);
    make_scale_button("csize", value_compressed_size);
    make_scale_button("isize", value_installed_size);

    var make_group_button = function(name, order) {
        var button_id = chart_id + "-" + name;
        d3.select(button_id).on("click", function() {
            fetch_for_ordering(order);

            /* drop off the '#' sign to convert id to a class prefix */
            d3.selectAll("." + chart_id.substring(1) + "-groupby")
                .classed("active", false);
            d3.select(button_id).classed("active", true);
        });
    };

    jQuery.each(orderings, function(k, v) {
        make_group_button(k, v);
    });

    /* adapt the chart size when the browser resizes */
    var resize_timeout = null;
    var real_resize = function() {
        resize_timeout = null;
        d3_div.selectAll("div")
            .data(treemap.size([jq_div.width(), jq_div.height()]), key_func)
            .call(cell);
    };
    jQuery(window).resize(function() {
        if (resize_timeout) {
            clearTimeout(resize_timeout);
        }
        resize_timeout = setTimeout(real_resize, 200);
    });
}

function developer_keys(chart_id, data_url) {
    var jq_div = jQuery(chart_id),
        r = 10;

    var force = d3.layout.force()
        .friction(0.5)
        .gravity(0.1)
        .charge(-500)
        .size([jq_div.width(), jq_div.height()]);

    var svg = d3.select(chart_id)
        .append("svg");

    d3.json(data_url, function(json) {
        var fill = d3.scale.category20();

        var index_for_key = function(key) {
            var i;
            key = key.slice(-8);
            for (i = 0; i < json.nodes.length; i++) {
                var node_key = json.nodes[i].key;
                if (node_key && node_key.slice(-8) === key) {
                    return i;
                }
            }
        };

        /* filter edges to only include those that we have two nodes for */
        var edges = jQuery.grep(json.edges, function(d, i) {
            d.source = index_for_key(d.signer);
            d.target = index_for_key(d.signee);
            return d.source >= 0 && d.target >= 0;
        });

        jQuery.map(json.nodes, function(d, i) { d.master_sigs = 0; d.other_sigs = 0; });
        jQuery.map(edges, function(d, i) {
            /* only the target gets credit in either case, as it is their key that was signed */
            if (json.nodes[d.source].group === "master") {
                json.nodes[d.target].master_sigs += 1;
            } else {
                json.nodes[d.target].other_sigs += 1;
            }
        });
        jQuery.map(json.nodes, function(d, i) {
            if (d.group === "dev" || d.group === "tu") {
                d.approved = d.master_sigs >= 3;
            } else {
                d.approved = null;
            }
        });

        var link = svg.selectAll("line")
            .data(edges)
            .enter()
            .append("line")
            .style("stroke", "#888");

        /* anyone with more than 7 - 1 == 6 signatures gets the top value */
        var stroke_color_scale = d3.scale.log().domain([1, 7]).range(["white", "green"]).clamp(true);

        var node = svg.selectAll("circle")
            .data(json.nodes)
            .enter().append("circle")
            .attr("r", function(d) {
                switch (d.group) {
                case "master":
                    return r * 1.6 - 0.75;
                case "cacert":
                    return r * 1.4 - 0.75;
                case "dev":
                case "tu":
                default:
                    return r - 0.75;
                }
            })
            .style("fill", function(d) { return fill(d.group); })
            .style("stroke", function(d) {
                if (d.approved === null) {
                    return d3.rgb(fill(d.group)).darker();
                } else if (d.approved) {
                    /* add 1 so we don't blow up the logarithm-based scale */
                    return stroke_color_scale(d.other_sigs + 1);
                } else {
                    return "red";
                }
            })
            .style("stroke-width", "1.5px")
            .call(force.drag);
        node.append("title").text(function(d) { return d.name; });

        var nodeover = function(d, i) {
            d3.select(this).transition().duration(500).style("stroke-width", "3px");
            link.filter(function(d_link, i) {
                return d_link.source === d || d_link.target === d;
            }).transition().duration(500).style("stroke", "#800");
        };
        var nodeout = function(d, i) {
            d3.select(this).transition().duration(500).style("stroke-width", "1.5px");
            link.transition().duration(500).style("stroke", "#888");
        };

        node.on("mouseover", nodeover)
            .on("mouseout", nodeout);

        var distance = function(d, i) {
            /* place a long line between all master keys and other keys.
             * however, other connected clusters should be close together. */
            if (d.source.group === "master" || d.target.group === "master" ||
                    d.source.group === "cacert" || d.target.group === "cacert") {
                return 200;
            } else {
                return 40;
            }
        };

        var strength = function(d, i) {
            if (d.source.group === "master" || d.target.group === "master" ||
                    d.source.group === "cacert" || d.target.group === "cacert") {
                return 0.2;
            } else {
                return 0.8;
            }
        };

        var tick = function() {
            var offset = r * 2,
                w = jq_div.width(),
                h = jq_div.height();
            node.attr("cx", function(d) { return (d.x = Math.max(offset, Math.min(w - offset, d.x))); })
                .attr("cy", function(d) { return (d.y = Math.max(offset, Math.min(h - offset, d.y))); });

            link.attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });
        };

        force.nodes(json.nodes)
            .links(edges)
            .linkDistance(distance)
            .linkStrength(strength)
            .on("tick", tick)
            .start();
    });

    /* adapt the chart size when the browser resizes */
    var resize_timeout = null;
    var real_resize = function() {
        resize_timeout = null;
        force.size([jq_div.width(), jq_div.height()]);
    };
    jQuery(window).resize(function() {
        if (resize_timeout) {
            clearTimeout(resize_timeout);
        }
        resize_timeout = setTimeout(real_resize, 200);
    });
}
