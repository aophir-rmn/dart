var dartApp = angular.module(
    'dartApp',
    [
        'ngMaterial', 'ui.router', 'ngResource', 'schemaForm', 'md.data.table', 'angularUtils.directives.uiBreadcrumbs',
        'dart.controllers.entities',
        'dart.controllers.managers',
        'dart.controllers.entity_modal',
        'dart.controllers.dataset_guess_modal',
        'dart.controllers.dataset_guess_entity_modal',
        'dart.controllers.graph_load_modal',
        'dart.controllers.header',
        'dart.controllers.navbar',
        'dart.controllers.tools',
        'dart.directives.create_new',
        'dart.directives.graph',
        'dart.directives.tables',
        'dart.services.entities',
        'dart.services.entity_modal',
        'dart.services.dataset_guess_modal',
        'dart.services.dataset_guess_entity_modal',
        'dart.services.filter',
        'dart.services.graph',
        'dart.services.graph_load_modal',
        'dart.services.utils'
    ]
);

dartApp.config(['$stateProvider', '$urlRouterProvider', 'schemaFormProvider', function($stateProvider, $urlRouterProvider, schemaFormProvider) {

    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/startsWith
    if (!String.prototype.startsWith) {
      String.prototype.startsWith = function(searchString, position) {
        position = position || 0;
        return this.indexOf(searchString, position) === position;
      };
    }

    $urlRouterProvider.otherwise('/dashboard');

    $stateProvider
        .state('app', {
            url: '/',
            abstract: true,
            views: {
                'header': {
                    templateUrl: 'static/partials/header.html',
                    controller: 'HeaderController'
                },
                'navbar': {
                    templateUrl: 'static/partials/navbar.html',
                    controller: 'NavbarController'
                },
                'content': {
                    template: '<i>loading...</i>'
                },
                'footer': {
                    templateUrl: 'static/partials/footer.html'
                }
            }
        })
        .state('app.dashboard', {
            url: 'dashboard',
            views: {
                'content@': {
                    templateUrl: 'static/partials/dashboard.html'
                    //controller: 'DatastoresController'
                }
            },
            data: { displayName: 'dashboard'}
        })
        .state('app.managers', {
            url: 'managers/',
            views: {
                'content@': {
                    template: '<h3>choose a manager from the navbar :D</h3>'
                }
            },
            data: { displayName: 'managers'}
        })
        .state('app.managers.datastore', {
            url: 'datastore?id&af&wf&wif&t',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/managers/datastore.html',
                    controller: 'DatastoreManagerController'
                }
            },
            data: { displayName: 'datastore'}
        })
        .state('app.managers.workflow', {
            url: 'workflow?id&wif&df&af&tf&t',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/managers/workflow.html',
                    controller: 'WorkflowManagerController'
                }
            },
            data: { displayName: 'workflow'}
        })
        .state('app.entities', {
            url: 'entities/',
            views: {
                'content@': {
                    template: '<h3>choose an entity from the navbar :D</h3>'
                }
            },
            data: { displayName: 'entities'}
        })
        .state('app.entities.engines', {
            url: 'engines',
            views: {
                'content@': {
                    templateUrl: 'static/partials/entities/engines.html',
                    controller: 'EnginesEntityController'
                }
            },
            data: { displayName: 'engines'}
        })
        .state('app.entities.datasets', {
            url: 'datasets?f',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/entities/datasets.html',
                    controller: 'DatasetsEntityController'
                }
            },
            data: { displayName: 'datasets'}
        })
        .state('app.entities.datastores', {
            url: 'datastores?f',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/entities/datastores.html',
                    controller: 'DatastoresEntityController'
                }
            },
            data: { displayName: 'datastores'}
        })
        .state('app.entities.actions', {
            url: 'actions?f',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/entities/actions.html',
                    controller: 'ActionsEntityController'
                }
            },
            data: { displayName: 'actions'}
        })
        .state('app.entities.workflows', {
            url: 'workflows?f',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/entities/workflows.html',
                    controller: 'WorkflowsEntityController'
                }
            },
            data: { displayName: 'workflows'}
        })
        .state('app.entities.workflow_instances', {
            url: 'workflow_instances?f',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/entities/workflow_instances.html',
                    controller: 'WorkflowInstancesEntityController'
                }
            },
            data: { displayName: 'workflow instances'}
        })
        .state('app.entities.subscriptions', {
            url: 'subscriptions?f',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/entities/subscriptions.html',
                    controller: 'SubscriptionsEntityController'
                }
            },
            data: { displayName: 'subscriptions'}
        })
        .state('app.entities.triggers', {
            url: 'triggers?f',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/entities/triggers.html',
                    controller: 'TriggersEntityController'
                }
            },
            data: { displayName: 'triggers'}
        })
        .state('app.entities.trigger_types', {
            url: 'trigger_types',
            views: {
                'content@': {
                    templateUrl: 'static/partials/entities/trigger_types.html',
                    controller: 'TriggerTypesEntityController'
                }
            },
            data: { displayName: 'trigger types'}
        })
        .state('app.entities.events', {
            url: 'events?f',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/entities/events.html',
                    controller: 'EventsEntityController'
                }
            },
            data: { displayName: 'events'}
        })
        .state('app.tools', {
            url: 'tools/',
            views: {
                'content@': {
                    template: '<h3>choose a tool from the navbar :D</h3>'
                }
            },
            data: { displayName: 'tools'}
        })
        .state('app.tools.graph', {
            url: 'graph?t&id',
            reloadOnSearch: false,
            views: {
                'content@': {
                    templateUrl: 'static/partials/tools/graph.html',
                    controller: 'GraphController'
                }
            },
            data: { displayName: 'graph'}
        })
    ;
}]);
