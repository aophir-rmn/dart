angular
    .module('dart.controllers.dataset_guess_entity_modal', [])
    .controller('DatasetGuessEntityModalController', ['$scope', '$mdDialog', 'entity', 'getSchema', 'getDatasetGuess', 'saveEntity',
        function($scope, $mdDialog, entity, getSchema, getDatasetGuess, saveEntity) {
            $scope.form = ["*"];
            $scope.entity = entity;
            $scope.showSave = saveEntity;
            getDatasetGuess(entity).then(function(response) {
                    $scope.entity = response.results;
                });
            getSchema().then(function (response) {
                    $scope.schema = response.results;
                });
            $scope.onCancel = function() { $mdDialog.hide(); };
            $scope.onSubmit = function(entity, form) {
                $scope.working = true;
                $scope.$broadcast('schemaFormValidate');
                if (!form.$valid) {
                    $scope.working = false;
                    return
                }
                saveEntity(entity)
                    .then(function(response) {
                        $scope.working = false;
                        entity = response.results;
                        $mdDialog.hide();
                    });
            }
        }
    ])
;
