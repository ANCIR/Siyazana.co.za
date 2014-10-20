$(function() {
  var apiEndpoint = null,
      element = null,
      nodes = {}, links = {},
      vis = null, node = null, path = null, path_group = null,
      w = null, h = null, min_r = null, max_r = null;

  var d3cola = cola.d3adaptor();

  var init = function(el, entityId) {
    
    var timeout = null;
    $(window).resize(function() {
      window.clearTimeout(timeout);
      timeout = window.setTimeout(function() {
        updateViz();
      }, 300);
    });
    
    element = el;
    vis = d3.select(element).append("svg");
    path_group = vis.append("svg:g");
  };

  var updateViz = function() {
    w = $(element).width();
    h = $(element).height();
    $(element).find('svg').height(h).width(w);
    max_r = w * (1/30);
    min_r = 0.3 * max_r;

    d3cola.linkDistance(max_r * 2)
        //.symmetricDiffLinkLengths(max_r * 4)
        //.avoidOverlaps(true)
        .size([w, h]);


    var graph = updateGraph();
        scale = radiusScale();

    var getRadius = function(d) {
      d.radius = scale(d.degree || 0);
      return d.radius;
    };
    
    d3cola
      .nodes(graph.nodes)
      .links(graph.links)
      .start(10, 15, 20);

    path = path_group.selectAll("path")
      .data(d3cola.links());

    path.enter().append("svg:path")
      .attr("class", "link");

    path.exit().remove();

    vis.selectAll(".node").remove();

    node = vis.selectAll(".node")
        .data(d3cola.nodes())
      .enter().append("g")
        .attr("class", "node")
        .on('dragstart', function(d) {
            d3.event.sourceEvent.stopPropagation();
        })
        //.on('click', expandNode)
        //.on('dblclick', viewNode)
        //.on('mouseenter', mouseEnter)
        //.on('mouseleave', mouseLeave)
        .call(d3cola.drag);

    node.append('svg:circle')
      //.style('fill', getColor)
      .attr('tooltip-append-to-body', true)
      .attr('tooltip-placement', 'top')
      .attr('tooltip', function(d) { return d.name; })
      .attr('r', getRadius);

    var cutoff = (max_r - min_r) * 0.5;
    node.filter(function(d) { return d.radius > cutoff; })
      .append("text")
      .attr("x", -12)
      .attr("dy", ".4em")
      .text(function(d) { return d.name.length > 50 ? d.name.slice(0, 50) + '...' : d.name; });
  };

  d3cola.on('tick', function() {
    path.attr("d", function(d) {
      var dx = d.target.x - d.source.x,
          dy = d.target.y - d.source.y,
          dr = Math.sqrt(dx * dx + dy * dy);
      return "M" + 
          d.source.x + "," + 
          d.source.y + "A" + 
          dr + "," + dr + " 0 0,1 " + 
          d.target.x + "," + 
          d.target.y;
    });

    node
      .attr("transform", function(d) {
        d.x = Math.max(d.radius, Math.min(w - d.radius, d.x));
        d.y = Math.max(d.radius, Math.min(h - d.radius, d.y));
        return "translate(" + d.x + "," + d.y + ")";
      });
  });

  function updateGraph() {
    var nodeList = [],
        linkList = [],
        nodeIndexes = {};

    for (var nodeId in nodes) {
      if (nodeIndexes[nodeId] === undefined) {
          nodeList.push(nodes[nodeId]);
          nodeIndexes[nodeId] = nodeList.length - 1;    
      }
    }    
  
    for (var linkId in links) {
      link = links[linkId];
      linkList.push({
        source: nodeIndexes[link.source],
        target: nodeIndexes[link.target],
        schema: link.schema,
        id: link.id
      });
    }    

    return {
      'nodes': nodeList,
      'links': linkList
    }
  }

  function radiusScale() {
    var min_deg = 10000, max_deg = 0;
    for (var i in nodes) {
      var d = nodes[i].degree;
      if (d > max_deg) {
          max_deg = d;
      }
      if (d < min_deg) {
          min_deg = d;
      }
    }
    return d3.scale.linear()
      .domain([min_deg, max_deg])
      .rangeRound([min_r, max_r]);
  }

  var query = function(entityId) {
    var q = {
      'id': entityId,
      'schema': null,
      'degree': null,
      'properties': {'name': null},
      'relations': [{
        'schema': null,
        'reverse': null,
        'other': {
          'id': null,
          'degree': null,
          'schema': null,
          'properties': {'name': null}
        }
      }]
    };
    return $.getJSON(apiEndpoint + '/query', {'query': JSON.stringify(q)});
  };

  var handleResult = function(entityId, data) {
    // code from: 
    // https://github.com/granoproject/grano-ui/blob/master/grano/ui/static/js/directives/query_graph.js

    nodes = {},
    links = {};

    var getNodes = function(obj) {
      if (obj === null || obj === undefined) {
        return;
      }
      if ($.isArray(obj)) {
        return $.each(obj, function(i, o) { getNodes(o); });
      }

      $.each(['inbound', 'outbound', 'relations'], function(i, key) {
        getLinks(obj[key], obj.id);
      });

      nodes[obj.id] = {
        'id': obj.id,
        'isRoot': false,
        'schema': obj.schema,
        'degree': obj.degree,
        'name': obj.properties.name.value
      };
    };

    var getLinks = function(obj, parent) {
      if (obj === null || obj === undefined) {
        return;
      }
      if ($.isArray(obj)) {
        return $.each(obj, function(i, o) { getLinks(o, parent); });
      }

      var child_id = null;
      $.each(['source', 'target', 'other'], function(i, key) {
        getNodes(obj[key]);
        if (obj[key] !== undefined) {
          child_id = obj[key].id;
        }
      });

      links[obj.id] = {
        'id': obj.id,
        'schema': obj.schema.name,
        'source': obj.reverse ? child_id : parent,
        'target': obj.reverse ? parent : child_id
      };
    };
    
    getNodes(data.results);
    updateViz();
  };

  $('#graph-viz').each(function(i, graph) {
    var entityId = $(graph).data('entity-id');
    apiEndpoint = $(graph).data('api-endpoint');
    //console.log(graph, entityId, apiEndpoint);
    init(graph, entityId);
    query(entityId).then(function(data) {
      handleResult(entityId, data);
    });
  });

});
