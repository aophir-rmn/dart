angular
    .module('dart.controllers.entity_modal', [])
    .controller('EntityModalController', ['$scope', '$mdDialog', 'entity', 'getSchema', 'saveEntity',
        function($scope, $mdDialog, entity, getSchema, saveEntity) {
            $scope.form = ["*"];
            $scope.entity = entity;
            $scope.showSave = saveEntity;
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
