angular
    .module('dart.services.entities')
    .factory('DatasetService', ['$resource', 'dtUtils', 'EntityModalService', function($resource, Utils) {
        function api() { return $resource('api/1/dataset/:id', null, { 'update': { method: 'PUT' }}) }
        return {
            getSchema: function() {return Utils.wrap($resource('api/1/schema/dataset').get().$promise)},
            getDatasetGuess: function(e) {return Utils.wrap($resource('api/1/dataset/guess').get({s3_path: e.s3_path, max_lines: e.max_lines}).$promise)},
            getDatasetGuessSchema: function() { return Utils.wrap($resource('api/1/schema/dataset/guess').get().$promise) },
            getEntity: function(id) { return Utils.wrap(api().get({id: id}).$promise) },
            getEntities: function(limit, offset, filters) { return Utils.wrap(api().get({limit: limit, offset: offset, filters: JSON.stringify(filters)}).$promise) },
            saveEntity: function(e) { return Utils.wrap(api().save(null, Utils.stripSingleArrayElementNulls(e)).$promise, true) },
            updateEntity: function(e) { return Utils.wrap(api().update({id: e.id }, Utils.stripSingleArrayElementNulls(e)).$promise, true) },
        };
    }])
;
