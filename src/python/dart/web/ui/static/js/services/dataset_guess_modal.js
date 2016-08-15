angular
    .module('dart.services.dataset_guess_modal', [])
    .factory('DatasetGuessModalService', ['$mdDialog', function($mdDialog) {
        return {
            showDialog: function showDialog(ev, entity, getDatasetGuessSchema, getDatasetGuess) {
                $mdDialog.show({
                    controller: 'DatasetGuessModalController',
                    templateUrl: 'static/partials/dataset_guess_modal.html',
                    parent: angular.element(document.body),
                    targetEvent: ev,
                    clickOutsideToClose: true,
                    locals: {entity: entity, getDatasetGuessSchema: getDatasetGuessSchema, getDatasetGuess: getDatasetGuess}
                })
            }
        }
    }])
;
