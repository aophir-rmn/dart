angular
    .module('dart.directives.tables')
    .directive('dtDatasetsTable', [function() {
        return {
            restrict: 'E',
            scope: {
                options: '='
            },
            templateUrl: 'static/partials/directives/tables/datasets.html',
            controller: ['$scope', 'DatasetService', 'EntityModalService', 'FilterService', '$state',
                function($scope, DatasetService, EntityModalService, FilterService, $state) {
                    $scope.$state = $state;
                    $scope.filters = $scope.options.filters || [];
                    $scope.$watchCollection("filters", function (newCollection, oldCollection) {
                            if (newCollection.length === 0 && oldCollection.length === 0) { return }
                            $scope.onPaginationChange(1, $scope.query.limit);
                        }
                    );
                    $scope.query = { limit: 10, page: 1 };
                    $scope.onPaginationChange = function(page, limit) {
                        if ($scope.options.onTableChange) {
                            $scope.options.onTableChange(page, limit, $scope.filters)
                        }
                        $scope.$p = DatasetService.getEntities(limit, (page - 1) * limit, $scope.filters);
                        $scope.$p.then(function(response) { $scope.response = response });
                        return $scope.$p;
                    };
                    $scope.onPaginationChange(1, $scope.query.limit);
                    $scope.showEntityModal = function(ev, entity, mode) {
                        var e = entity;
                        if (mode === 'duplicate') {
                            e = { data: JSON.parse(JSON.stringify(entity.data)) };
                        }
                        var saveFunc = null;
                        if (mode === 'edit') {
                            saveFunc = function (entity) { return DatasetService.updateEntity(entity).then(function(e) { entity = e; return e }) }
                        }
                        if (mode === 'duplicate') {
                            saveFunc = function (entity) { return DatasetService.saveEntity(entity) }
                        }
                        EntityModalService.showDialog(ev, e, false,
                            function () {
                                return DatasetService.getSchema().then(function(response) {
                                    if (mode === 'view') {
                                        response.results.readonly = true;
                                    }
                                    return response
                                })
                            },
                            null,
                            saveFunc
                        )
                    };
                    DatasetService.getSchema().then(function(response) {
                        $scope.getFilterChoices = function(searchText) { return FilterService.getFilterChoices(searchText, [response.results]) };
                    });
                }
            ]
        }
    }])
;