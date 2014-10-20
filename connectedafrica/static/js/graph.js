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

    

    $('#graph-viz').each(function(i, graph) {
      var entityId = $(graph).data('entity-id');
      apiEndpoint = $(graph).data('api-endpoint');
      console.log(graph, entityId, apiEndpoint);
      query(entityId).then(function(data) {
        console.log(data.results);
      });
    });
});
