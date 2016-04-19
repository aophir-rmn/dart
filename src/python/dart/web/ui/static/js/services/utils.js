angular
    .module('dart.services.utils', [])
    .factory('dtUtils', ['$mdToast', '$mdDialog', '$window',
        function($mdToast, $mdDialog, $window) {
            function stripSingleArrayElementNulls(obj) {
                for (var property in obj) {
                    if (obj.hasOwnProperty(property)) {
                        var value = obj[property];
                        if (Array.isArray(value) && value.length === 1 &&
                            (value[0] === null || typeof value[0] === "undefined" || value[0] === '')
                        ) {
                            obj[property] = []

                        } else if (typeof value == "object") {
                            stripSingleArrayElementNulls(value);
                        }
                    }
                }
            }
            return {
                stripSingleArrayElementNulls: function(obj) {
                    stripSingleArrayElementNulls(obj);
                    return obj
                },
                wrap: function($promise, showSuccessToast) {
                    return $promise.then(
                        function(response) {
                            if (showSuccessToast) {
                                var toast = $mdToast
                                    .simple()
                                    .content('Success!')
                                    .position('top right')
                                    .hideDelay(3000)
                                $mdToast.show(toast);
                            }
                            return response
                        },
                        function(error) {
                            console.error(error);
                            var toast = $mdToast
                                .simple()
                                .content('Failed :(')
                                .position('top right')
                                .hideDelay(30000)
                                .action('More Info');
                            $mdToast.show(toast).then(function(response) {
                                if ( response == 'ok' ) {
                                    var errorText;
                                    errorText = ( error.data ? error.data : 'An unknown error occurred' );
                                    $mdDialog.show($mdDialog
                                        .alert()
                                        .title('Error')
                                        .textContent(errorText)
                                        .ok('OK')
                                    );
                                }
                            });
                            return error
                        }
                    );
                },
                extend: function(o1, o2) {
                    // http://stackoverflow.com/questions/14843815/recursive-deep-extend-assign-in-underscore-js
                    var deep = function(a, b) {
                        return $window._.isObject(a) && _.isObject(b) ? _.extend(a, b, deep) : b;
                    };
                    return $window._.extend(o1, o2, deep);
                }
            }
        }])
;
