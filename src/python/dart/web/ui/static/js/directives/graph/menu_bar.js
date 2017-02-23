angular
    .module('dart.directives.graph')
    .directive('dtGraphMenuBar', [function() {
        return {
            restrict: 'E',
            scope: {
                options: '='
            },
            templateUrl: 'static/partials/directives/graph/menu_bar.html',
            controller: ['$scope', '$state', 'EntityModalService', 'GraphService', 'ActionService', 'DatasetService', 'DatastoreService',
                'EventService', 'SubscriptionService', 'TriggerService', 'WorkflowService', 'WorkflowInstanceService', '$q', '$timeout',
                '$window', 'GraphLoadModalService', 'dtUtils', '$mdDialog',
                function($scope, $state, EntityModalService, GraphService, ActionService, DatasetService, DatastoreService,
                         EventService, SubscriptionService, TriggerService, WorkflowService, WorkflowInstanceService, $q,
                         $timeout, $window, GraphLoadModalService, dtUtils, $mdDialog) {

                    $scope._ = $window._;

                    $scope.reset = function() {
                        $scope.subGraphCounter = 0;
                        $scope.activeSubGraphEntityMaps = {};
                        $scope.relatedNodes = {};
                        $scope.editOperations = [];
                    };

                    $scope.nodeId = function(node) { return node.entity_type + '-' + node.entity_id };

                    $scope.subGraphEntityMap = function(node) {
                        return $scope.activeSubGraphEntityMaps[node.engine_name][node.sub_graph_name];
                    };

                    $scope.subGraphEntity = function(node) {
                        var nodeId = $scope.nodeId(node);
                        return $scope.subGraphEntityMap(node)[nodeId];
                    };

                    $scope.nodeData = function(entity, entityType, entityId) {
                        return {
                            entity_type: entityType,
                            entity_id: entityId,
                            name: entity.data.name,
                            state: entity.data.state
                        }
                    };

                    $scope.showGraphLoadModal = function(ev) {
                        GraphLoadModalService.showDialog(ev, $scope.options.onSelectedItemChange)
                    };

                    $scope.saveGraph = function(ev) {
                        var unsavedEntities = {};
                        _.each($scope.activeSubGraphEntityMaps, function(entityMapsByName) {
                            _.each(entityMapsByName, function(entityMap) {
                                _.assign(unsavedEntities, entityMap);
                            });
                        });
                        _.each(unsavedEntities, function(entity, entity_id) {
                            unsavedEntities[entity_id] = dtUtils.stripSingleArrayElementNulls(entity)
                        });

                        var entityMap = {unsaved_entities: unsavedEntities, related_entity_data: $scope.relatedNodes};
                        GraphService.saveEntityMap(entityMap, true).then(function(response) {
                            if (response.data && response.data.results === 'ERROR') {
                                $scope.errorMessage = response.data.error_message;
                                $scope.$root.$broadcast('dt-graph-save-failed', JSON.parse($scope.errorMessage));
                                return
                            }
                            $scope.reset();
                            $scope.$root.$broadcast('dt-graph-reload');
                        })
                    };

                    $scope.$on('dt-graph-node-selected', function(evt, current_node) {
                        if ($scope.selectedNode && $scope.nodeId($scope.selectedNode) === $scope.nodeId(current_node)) {
                            return
                        }

                        $timeout(function () {
                            $scope.editOperations = [];
                            if (current_node.entity_type === 'workflow' && !current_node.entity_id.startsWith('UNSAVED')) {
                                $scope.editOperations.push({
                                    name: 'run',
                                    description: 'manually run workflow',
                                    md_icon: 'directions_run',
                                    func: function() { WorkflowService.manuallyRunWorkflow(current_node.entity_id) }
                                })
                            }
                            if (current_node.entity_type === 'action' && current_node.state === 'TEMPLATE') {
                                $scope.editOperations.push({
                                    name: 'delete',
                                    description: 'delete this workflow step',
                                    md_icon: 'delete',
                                    func: function() {
                                        var confirm = $mdDialog.confirm()
                                            .title('Are you sure you want to delete this workflow step?')
                                            .content('This cannot be undone.')
                                            .ariaLabel('delete')
                                            .ok('ok')
                                            .cancel('cancel')
                                            .targetEvent(evt);
                                        $mdDialog.show(confirm).then(function() {
                                            if (current_node.entity_id.startsWith('UNSAVED')) {
                                                delete $scope.subGraphEntityMap(current_node)[$scope.nodeId(current_node)];
                                                $scope.$root.$broadcast('dt-graph-remove-node', current_node);
                                                return
                                            }
                                            ActionService.deleteEntity(current_node.entity_id).then(function() {
                                                $scope.reset();
                                                $scope.$root.$broadcast('dt-graph-reload');
                                            });
                                        });
                                    }
                                })
                            }
                            $scope.selectedNode = current_node;
                            $scope.loadSubGraphMap();
                        });
                    });
                    $scope.$on('dt-graph-node-unselected', function(evt) {
                        $timeout(function () {
                            $scope.selectedNode = null;
                            $scope.subGraphMap = null;
                            $scope.editOperations = [];
                            $scope.loadSubGraphMap();
                        });
                    });

                    $scope.loadSubGraphMap = function() {
                        var entityType = $scope.selectedNode ? $scope.selectedNode.entity_type : null;
                        var engineName = $scope.selectedNode ? $scope.selectedNode.engine_name : null;
                        var relatedId = $scope.selectedNode ? $scope.selectedNode.entity_id : null;
                        if (relatedId && relatedId.startsWith('UNSAVED-')) {
                            relatedId = null;
                        }
                        GraphService.getSubGraphMap(entityType, relatedId, engineName).then(function(response) {
                            $scope.noEngineSubGraphs = response.results[null];
                            $scope.subGraphMap = response.results;
                            delete $scope.subGraphMap[null]
                        });
                    };

                    $scope.reset();

                    $scope.addSubGraph = function(engine_name, subGraphFromServer) {
                        var subGraph = JSON.parse(JSON.stringify(subGraphFromServer));
                        var graph = subGraph.graph;

                        if (!$scope.activeSubGraphEntityMaps[engine_name]) { $scope.activeSubGraphEntityMaps[engine_name] = {} }
                        if (!$scope.activeSubGraphEntityMaps[engine_name][subGraph.name]) { $scope.activeSubGraphEntityMaps[engine_name][subGraph.name] = {} }
                        _.assign($scope.activeSubGraphEntityMaps[engine_name][subGraph.name], subGraph.entity_map);

                        $scope.subGraphCounter++;
                        _.each(graph.nodes, function(e) {
                            e.engine_name = engine_name;
                            e.sub_graph_name = subGraph.name;

                            // this is because the angular-schema-form library has issues applying defaults to null objects
                            var entity = $scope.subGraphEntity(e);
                            if (!entity.data.args) { delete entity.data.args; }
                        });
                        var prop = null;
                        if (subGraph.related_is_a) {
                            if (subGraph.related_is_a == 'PARENT') { prop = 'source_id' }
                            if (subGraph.related_is_a == 'CHILD')  { prop = 'destination_id' }
                            _.each(graph.edges, function(e) {
                                if (e[prop].startsWith(subGraph.related_is_a)) {
                                    $scope.relatedNodes[$scope.selectedNode.entity_type + '-' + e[prop]] = {
                                        entity_id: $scope.selectedNode.entity_id,
                                        entity_type: $scope.selectedNode.entity_type,
                                        relationship: subGraph.related_is_a,
                                        edge: JSON.parse(JSON.stringify(e))
                                    };
                                    e[prop] = $scope.selectedNode.entity_id;
                                }
                            })
                        }
                        $scope.$root.$broadcast('dt-graph-add-sub-graph', graph);
                        $scope.loadSubGraphMap();
                    };

                    $scope.navigateToEntity = function() {
                        $state.go('app.entities.' + $scope.selectedNode.entity_type + 's', {f: JSON.stringify(['id=' + $scope.selectedNode.entity_id])})
                    };

                    $scope.onCancelChanges = function() {
                        $scope.reset();
                        $scope.loadSubGraphMap();
                        $scope.$root.$broadcast('dt-graph-cancel-sub-graph');
                    };

                    var getEntityMap = {
                        'action': function(entity_id) { return ActionService.getEntity(entity_id) },
                        'dataset': function(entity_id) { return DatasetService.getEntity(entity_id) },
                        'datastore': function(entity_id) { return DatastoreService.getEntity(entity_id) },
                        'event': function(entity_id) { return EventService.getEntity(entity_id) },
                        'subscription': function(entity_id) { return SubscriptionService.getEntity(entity_id) },
                        'trigger': function(entity_id) { return TriggerService.getEntity(entity_id) },
                        'workflow': function(entity_id) { return WorkflowService.getEntity(entity_id) },
                        'workflow_instance': function(entity_id) { return WorkflowInstanceService.getEntity(entity_id) }
                    };
                    var updateEntityMap = {
                        'action': function(entity) { return ActionService.updateEntity(entity) },
                        'dataset': function(entity) { return DatasetService.updateEntity(entity) },
                        'datastore': function(entity) { return DatastoreService.updateEntity(entity) },
                        'event': function(entity) { return EventService.updateEntity(entity) },
                        'subscription': function(entity) { return SubscriptionService.updateEntity(entity) },
                        'trigger': function(entity) { return TriggerService.updateEntity(entity) },
                        'workflow': function(entity) { return WorkflowService.updateEntity(entity) }
                    };
                    var getSchemaMap = {
                        'action': function(entity_id) { return ActionService.getSchema({entity_id: entity_id}) },
                        'dataset': function() { return DatasetService.getSchema() },
                        'datastore': function(entity_id) { return DatastoreService.getSchema({entity_id: entity_id}) },
                        'event': function() { return EventService.getSchema() },
                        'subscription': function() { return SubscriptionService.getSchema() },
                        'trigger': function(entity_id) { return TriggerService.getSchema({entity_id: entity_id}) },
                        'workflow': function() { return WorkflowService.getSchema() },
                        'workflow_instance': function() { return WorkflowInstanceService.getSchema() }
                    };
                    var getNewSchemaMap = {
                        'action': function() {
                            return ActionService.getSchema({
                                engine_name: $scope.selectedNode.engine_name,
                                action_type_name: $scope.subGraphEntity($scope.selectedNode).data.action_type_name
                            })
                        },
                        'dataset': function() { return DatasetService.getSchema() },
                        'datastore': function() { return DatastoreService.getSchema({engine_name: $scope.selectedNode.engine_name}) },
                        'event': function() { return EventService.getSchema() },
                        'subscription': function() { return SubscriptionService.getSchema() },
                        'trigger': function() {
                            return TriggerService.getSchema({
                                trigger_type_name: $scope.subGraphEntity($scope.selectedNode).data.trigger_type_name
                            })
                        },
                        'workflow': function() { return WorkflowService.getSchema() },
                        'workflow_instance': function() { return WorkflowInstanceService.getSchema() }
                    };

                    var showViewExistingEntityModal = function(ev) {
                        $q.all([
                            getEntityMap[$scope.selectedNode.entity_type]($scope.selectedNode.entity_id),
                            getSchemaMap[$scope.selectedNode.entity_type]($scope.selectedNode.entity_id)
                        ]).then(function(responses) {
                            var entity = responses[0].results;
                            EntityModalService.showDialog(ev, entity,
                                function getSchema() {
                                    var deferred = $q.defer();
                                    responses[1].results.readonly = true;
                                    deferred.resolve(responses[1]);
                                    return deferred.promise;
                                },
                                null
                            )
                        });
                    };
                    var showEditExistingEntityModal = function(ev) {
                        var entityType = $scope.selectedNode.entity_type;
                        var entityId = $scope.selectedNode.entity_id;
                        $q.all([
                            getEntityMap[entityType](entityId),
                            getSchemaMap[entityType](entityId)
                        ]).then(function(responses) {
                            var entity = responses[0].results;
                            EntityModalService.showDialog(ev, entity,
                                function getSchema() {
                                    var deferred = $q.defer();
                                    deferred.resolve(responses[1]);
                                    return deferred.promise;
                                },
                                function updateEntity(entity) {
                                    return updateEntityMap[entityType](entity).then(function(response) {
                                        var nodeData = $scope.nodeData(response.results, entityType, entityId);
                                        $scope.$root.$broadcast('dt-graph-update-node-data', nodeData);
                                        return response;
                                    })
                                }
                            )
                        });
                    };
                    var showViewNewEntityModal = function(ev) {
                        var entityType = $scope.selectedNode.entity_type;
                        var entity = $scope.subGraphEntity($scope.selectedNode);
                        getNewSchemaMap[entityType]().then(function(response) {
                            EntityModalService.showDialog(ev, entity,
                                function getSchema() {
                                    var deferred = $q.defer();
                                    response.results.readonly = true;
                                    deferred.resolve(response);
                                    return deferred.promise;
                                },
                                null
                            );
                        })
                    };
                    var showEditNewEntityModal = function(ev) {
                        var entityType = $scope.selectedNode.entity_type;
                        var entityId = $scope.selectedNode.entity_id;
                        var entity = $scope.subGraphEntity($scope.selectedNode);
                        EntityModalService.showDialog(ev, entity,
                            getNewSchemaMap[entityType],
                            function saveEntity(entity) {
                                var nodeData = $scope.nodeData(entity, entityType, entityId);
                                var nodeId = $scope.nodeId($scope.selectedNode);
                                $scope.subGraphEntityMap($scope.selectedNode)[nodeId] = entity;
                                $scope.$root.$broadcast('dt-graph-update-node-data', nodeData);
                                var deferred = $q.defer();
                                deferred.resolve(entity);
                                return deferred.promise;
                            }
                        );
                    };

                    var showEntityModalMap = {
                        'view':     showViewExistingEntityModal,
                        'view/new': showViewNewEntityModal,
                        'edit':     showEditExistingEntityModal,
                        'edit/new': showEditNewEntityModal
                    };

                    $scope.showEntityModal = function(ev, mode) {
                        mode = $scope.selectedNode.entity_id.startsWith('UNSAVED') ? mode + '/new' : mode;
                        showEntityModalMap[mode](ev)
                    };

                    $scope.toggleLiveUpdatesEnabled = function() {
                        // needed due to angular material menuBar bug
                        $scope.liveUpdatesEnabled = !$scope.liveUpdatesEnabled;
                    };

                    $scope.liveUpdatesEnabled = true;
                    var timer;
                    function poll() {
                        if ($scope.liveUpdatesEnabled && $scope.subGraphCounter == 0) {
                            $scope.options.queryGraph().then(function(response) {
                                if (!response) { return }
                                $scope.$root.$broadcast('dt-graph-merge-graph', response.results);
                                timer = $timeout(poll, 30000);
                            });
                        }
                    }
                    timer = $timeout(poll, 30000);

                    $scope.$on('$destroy', function() { $timeout.cancel(timer) });

                    $scope.$watch('options.layout', function(newValue) {
                        $scope.$root.$broadcast('dt-graph-reset-layout', newValue);
                    });

                    $scope.resetLayout = function() {
                        $scope.$root.$broadcast('dt-graph-reset-layout', $scope.options.layout);
                    };
                }
            ]
        }
    }])
;
