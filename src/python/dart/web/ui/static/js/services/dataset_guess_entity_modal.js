angular
    .module('dart.services.dataset_guess_entity_modal', [])
    .factory('DatasetGuessEntityModalService', ['$mdDialog', function($mdDialog) {
        return {
            showDialog: function showDialog(ev, entity, getSchema, getDatasetGuess, saveEntity) {
                $mdDialog.show({
                    controller: 'DatasetGuessEntityModalController',
                    templateUrl: 'static/partials/dataset_guess_entity_modal.html',
                    parent: angular.element(document.body),
                    targetEvent: ev,
                    clickOutsideToClose: true,
                    locals: {entity: entity, getSchema: getSchema, getDatasetGuess: getDatasetGuess, saveEntity: saveEntity}
                })
            }
        }
    }])
;
