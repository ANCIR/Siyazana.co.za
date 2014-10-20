$(function() {
    var apiEndpoint = null;

    var query = function(entityId) {
      var q = q = {
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

      var queryNodes = {},
          queryLinks = {};

      var getNodes = function(obj) {
        if (obj === null || obj === undefined) {
          return;
        }
        if ($.isArray(obj)) {
          return $.each(obj, function(i, o) { getNodes(o); });
        }

        $.each(['inbound', 'outbound', 'relations'], function(i, key) {
          console.log(obj, key);
          getLinks(obj[key], obj.id);
        });

        queryNodes[obj.id] = {
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

        queryLinks[obj.id] = {
          'id': obj.id,
          'schema': obj.schema.name,
          'source': obj.reverse ? child_id : parent,
          'target': obj.reverse ? parent : child_id
        };
      };
      
      getNodes(data.results);
      updateViz(queryNodes, queryLinks);
    };

    var updateViz = function(nodes, links) {
      console.log(nodes, links);
    };

    $('#graph-viz').each(function(i, graph) {
      var entityId = $(graph).data('entity-id');
      apiEndpoint = $(graph).data('api-endpoint');
      console.log(graph, entityId, apiEndpoint);
      query(entityId).then(function(data) {
        handleResult(entityId, data);
      });
    });
});
