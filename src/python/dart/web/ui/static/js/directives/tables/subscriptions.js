angular
    .module('dart.directives.tables')
    .directive('dtSubscriptionsTable', [function() {
        return {
            restrict: 'E',
            scope: {
                options: '='
            },
            templateUrl: 'static/partials/directives/tables/subscriptions.html',
            controller: ['$scope', 'SubscriptionService', 'EntityModalService', 'FilterService', '$state',
                function($scope, SubscriptionService, EntityModalService, FilterService, $state) {
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
                        $scope.$p = SubscriptionService.getEntities(limit, (page - 1) * limit, $scope.filters);
                        $scope.$p.then(function(response) { $scope.response = response });
                        return $scope.$p;
                    };
                    $scope.onPaginationChange(1, $scope.query.limit);
                    $scope.showEntityModal = function(ev, entity, mode) {
                        var e = entity;
                        if (mode === 'duplicate') {
                            e = { data: JSON.parse(JSON.stringify(entity.data)) };
                            e.data.state = 'INACTIVE';
                            e.data.failed_time = null;
                            e.data.generating_time = null;
                            e.data.initial_active_time = null;
                            e.data.queued_time = null;
                        }
                        var saveFunc = null;
                        if (mode === 'edit') {
                            saveFunc = function (entity) { return SubscriptionService.updateEntity(entity).then(function(e) { entity = e; return e }) }
                        }
                        if (mode === 'duplicate') {
                            saveFunc = function (entity) { return SubscriptionService.saveEntity(entity) }
                        }
                        EntityModalService.showDialog(ev, e,
                            function () {
                                return SubscriptionService.getSchema().then(function(response) {
                                    if (mode === 'view') {
                                        response.results.readonly = true;
                                    }
                                    if (mode === 'edit') {
                                        // The following fields should be immutable for subscriptions
                                        response.results.properties.data.properties.s3_path_end_prefix_exclusive.readonly = true;
                                        response.results.properties.data.properties.s3_path_regex_filter.readonly = true;
                                        response.results.properties.data.properties.s3_path_start_prefix_inclusive.readonly = true;
                                    }
                                    return response
                                })
                            },
                            saveFunc
                        )
                    };
                    SubscriptionService.getSchema().then(function(response) {
                        $scope.getFilterChoices = function(searchText) { return FilterService.getFilterChoices(searchText, [response.results]) };
                    });
                }
            ]
        }
    }])
;