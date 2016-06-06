angular
    .module('dart.directives.create_new')
    .directive('dtDatasetsCreateNew', [function() {
        return {
            restrict: 'E',
            scope: {
                options: '='
            },
            templateUrl: 'static/partials/directives/create_new/datasets.html',
            controller: ['$scope', 'DatasetService', 'EntityModalService', 'DatasetGuessModalService',
                function($scope, DatasetService, EntityModalService, DatasetGuessModalService) {
                    $scope.form = ["*"];
                    $scope.onCreateNew = function(d) {
                        if (d.label === 'dataset') {
                            EntityModalService.showDialog(
                                null,
                                {},
                                function () { return DatasetService.getSchema() },
                                function (entity) { return DatasetService.saveEntity(entity) }
                            );
                        }
                        else if (d.label === 'dataset_from_existing_s3_path') {
                            DatasetGuessModalService.showDialog(
                                null,
                                {},
                                function () { return DatasetService.getDatasetGuessSchema() },
                                function (entity) { return DatasetService.getDatasetGuess(entity) }
                            );
                        }
                    };
                }
            ]
        }
    }])
;
