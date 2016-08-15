angular
    .module('dart.controllers.dataset_guess_modal', [])
    .controller('DatasetGuessModalController', ['$scope', '$mdDialog', 'entity', 'getDatasetGuessSchema', 'getDatasetGuess', 'DatasetService', 'DatasetGuessEntityModalService',
         function($scope, $mdDialog, entity, getDatasetGuessSchema, getDatasetGuess, DatasetService, DatasetGuessEntityModalService) {
            $scope.form = ["*"];
            $scope.entity = entity;
            $scope.showSave = true;

            getDatasetGuessSchema().then(function(response) { $scope.schema = response.results });
            $scope.onCancel = function() { $mdDialog.hide(); };
            $scope.onSubmitDatasetGuess = function(entity) {
                DatasetGuessEntityModalService.showDialog(
                    null,
                    entity,
                    function () {return DatasetService.getSchema() },
                    function (entity) { return DatasetService.getDatasetGuess(entity) },
                    function (entity) { return DatasetService.saveEntity(entity) }
                );
            }
        }
    ])
;
