angular
    .module('dart.directives.graph')
    .directive('dtGraph', [function() {
        return {
            restrict: 'E',
            scope: {
                options: '='
            },
            template :'<div id="cy" style="width:100%; position:relative; clear:both;" ng-style="{ height: graphHeight }"></div>',
            link: function(scope, element, attrs, fn) {

                scope.graphHeight = Math.round(angular.element(window).height() * 0.75);

                function colorMap(state) {
                    switch (state) {
                        case 'QUEUED': return 'yellow';
                        case 'PENDING': return 'yellow';
                        case 'RUNNING': return 'orange';
                        case 'FINISHING': return 'orange';
                        case 'GENERATING': return 'orange';
                        case 'COMPLETED': return 'green';
                        case 'FAILED': return 'red';
                        case 'SKIPPED': return 'black';
                        case 'ACTIVE': return 'blue';
                        case 'INACTIVE': return 'black';
                        case 'DONE': return '#66512c';
                        case 'HAS_NEVER_RUN': return 'grey';
                        case 'TEMPLATE': return 'grey';
                        default:
                            return 'grey'
                    }
                }

                function shapeMap(type) {
                    switch (type) {
                        case 'dataset': return 'rectangle';
                        case 'action': return 'ellipse';
                        case 'workflow': return 'diamond';
                        case 'workflow_instance': return 'diamond';
                        case 'trigger': return 'vee';
                        case 'subscription': return 'hexagon';
                        case 'datastore': return 'pentagon';
                        case 'event': return 'star';
                        default:
                            return 'octagon'
                    }
                }

                function nodeId(e) { return e.entity_type + '-' + e.entity_id }
                function edgeId(e) { return e.source_type + '-' + e.source_id + '-' + e.destination_type + '-' + e.destination_id }
                scope.nodeId = nodeId;
                scope.edgeId = edgeId;

                function cyNodeData(e) {
                    return {
                        entity_type: e.entity_type,
                        entity_id: e.entity_id,
                        name: e.name,
                        state: e.state,
                        sub_type: e.sub_type,
                        color: colorMap(e.state),
                        shape: shapeMap(e.entity_type),
                        id: nodeId(e),
                        engine_name: e.engine_name,
                        sub_graph_name: e.sub_graph_name
                    }
                }

                function cyEdgeData(e) {
                    return {
                        source: e.source_type + '-' + e.source_id,
                        target: e.destination_type + '-' + e.destination_id,
                        id: edgeId(e)
                    }
                }

                var layoutOptions = {
                    breadthfirst: {
                        name: 'breadthfirst',
                        animate: true,
                        animationDuration: 700,
                        animationEasing: 'ease-out'
                    },
                    circle: {
                        name: 'circle',
                        animate: true,
                        animationDuration: 700,
                        animationEasing: 'ease-out'
                    },
                    'cose-bilkent': {
                        name: 'cose-bilkent',
                        nodeRepulsion: 240000
                    },
                    dagre: {
                        name: 'dagre',
                        rankSep: 150,
                        animate: true,
                        animationDuration: 700,
                        animationEasing: 'ease-out'
                    },
                    grid: {
                        name: 'grid',
                        avoidOverlapPadding: 150,
                        animate: true,
                        animationDuration: 700,
                        animationEasing: 'ease-out'
                    }
                };
                scope.layout = scope.options.layout || 'dagre';

                var nodes = [];
                _.each(scope.options.nodes, function(e) {
                    nodes.push({data: cyNodeData(e)});
                });

                var edges = [];
                _.each(scope.options.edges, function(e) {
                    edges.push({data: cyEdgeData(e)})
                });

                // without the timeout, cytoscape will render before the angular template sets the height properly
                setTimeout(function() {
                    var cy = cytoscape({
                        container: document.getElementById('cy'),
                        boxSelectionEnabled: true,
                        autounselectify: false,
                        style: cytoscape.stylesheet()
                            .selector('node')
                            .css({
                                'height': 100,
                                'width': 100,
                                'font-size': 10,
                                'label': 'data(name)',
                                'text-wrap': 'wrap',
                                'text-outline-color': 'data(color)',
                                'background-color': 'data(color)',
                                'color': 'black',
                                'shape': 'data(shape)'
                            })
                            .selector('edge')
                            .css({
                                'width': 7,
                                'line-color': '#ffaaaa',
                                'target-arrow-shape': 'triangle',
                                'target-arrow-color': '#ffaaaa'
                            })
                            .selector(':selected')
                            .css({
                                'height': 200,
                                'width': 200,
                                'border-color': 'purple',
                                'border-width': 20
                            })
                            .selector('.faded')
                            .css({
                                'opacity': 0.20
                            }),
                        elements: { nodes: nodes, edges: edges },
                        layout: layoutOptions[scope.layout]
                    });

                    var lastSelectedNodeId = scope.options.selected_type + '-' + scope.options.selected_id;
                    cy.$('#' + lastSelectedNodeId).select();

                    cy.on('select', 'node', null, function(evt) {
                        var nodeData = evt.cyTarget.data();
                        var data = {
                            entity_type: nodeData.entity_type,
                            entity_id: nodeData.entity_id,
                            name: nodeData.name,
                            state: nodeData.state,
                            sub_type: nodeData.sub_type,
                            engine_name: nodeData.engine_name,
                            sub_graph_name: nodeData.sub_graph_name
                        };
                        lastSelectedNodeId = nodeId(nodeData);
                        scope.$root.$broadcast('dt-graph-node-selected', data);
                    });

                    cy.on('unselect', 'node', null, function(evt) {
                        lastSelectedNodeId = null;
                        scope.$root.$broadcast('dt-graph-node-unselected');
                    });

                    scope.$on('dt-graph-update-node-data', function(evt, node) {
                        var cyNode = cy.$('#' + lastSelectedNodeId);
                        var nodeData = cyNodeData(node);
                        _.defaults(nodeData, cyNode.data());
                        cyNode.data(nodeData);
                        scope.$root.$broadcast('dt-graph-node-selected', cyNode.data());
                    });

                    var subGraphsPresent = false;
                    scope.$on('dt-graph-add-sub-graph', function(evt, subGraph) {
                        if (!subGraphsPresent) { cy.elements().addClass('faded') }
                        cy.$('#' + lastSelectedNodeId).removeClass('faded');
                        subGraphsPresent = true;
                        var eles = [];
                        _.each(subGraph.nodes, function(e) {
                            var data = cyNodeData(e);
                            eles.push({group: "nodes", data: data, renderedPosition: {x: cy.width()/2, y: 1}});
                            cy.$('#' + data.id).removeClass('faded');
                        });
                        _.each(subGraph.edges, function(e) {
                            var data = cyEdgeData(e);
                            eles.push({group: "edges", data: data});
                            cy.$('#' + data.id).removeClass('faded');
                        });
                        cy.add(eles);
                        cy.layout(layoutOptions[scope.layout]);
                    });

                    function animatedRemoveElements(eles, onComplete, setPosition) {
                        var options = {
                            style: {'opacity': 0.2},
                            duration: 350,
                            easing: 'ease-out',
                            complete: function () {
                                cy.remove(eles);
                                if (onComplete) {
                                    onComplete()
                                }
                            }
                        };
                        setPosition ? options.position = {x: cy.width()/2, y: 1} : null;
                        eles.animate(options);
                    }

                    scope.$on('dt-graph-cancel-sub-graph', function(evt) {
                        subGraphsPresent = false;
                        animatedRemoveElements(cy.elements("[id *= 'UNSAVED']"), function() { cy.elements().removeClass('faded') });
                        cy.elements("[id !*= 'UNSAVED']").layout(layoutOptions[scope.layout]);
                        if (lastSelectedNodeId.indexOf('-UNSAVED') > -1) {
                            scope.$root.$broadcast('dt-graph-node-unselected');
                        }
                    });

                    scope.$on('dt-graph-merge-graph', function(evt, graph) {
                        var updatedNodesById = {};
                        var updatedEdgesById = {};
                        _.each(graph.nodes, function(e) { updatedNodesById[nodeId(e)] = e });
                        _.each(graph.edges, function(e) { updatedEdgesById[edgeId(e)] = e });

                        var nodesToRemove = [];
                        var existingNodeIds = [];
                        cy.nodes().each(function(i, e) {
                            var nodeId = e.id();
                            existingNodeIds.push(nodeId);
                            if (updatedNodesById[nodeId]) {
                                var data = cyNodeData(updatedNodesById[nodeId]);
                                e.data(data);
                                if (nodeId === lastSelectedNodeId) {
                                    scope.$root.$broadcast('dt-graph-node-selected', data);
                                }
                            } else {
                                nodesToRemove.push(e)
                            }
                        });
                        var edgesToRemove = [];
                        var existingEdgeIds = [];
                        cy.edges().each(function(i, e) {
                            var edgeId = e.id();
                            existingEdgeIds.push(edgeId);
                            updatedEdgesById[edgeId] ? e.data(cyEdgeData(updatedEdgesById[edgeId])) : edgesToRemove.push(e)
                        });
                        var newNodeIds = _.difference(_.keys(updatedNodesById), existingNodeIds);
                        var newEdgeIds = _.difference(_.keys(updatedEdgesById), existingEdgeIds);
                        var elesToAdd = [];
                        _.each(newNodeIds, function(nodeId) { elesToAdd.push({group: "nodes", data: cyNodeData(updatedNodesById[nodeId]), renderedPosition: {x: cy.width()/2, y: 1}}) });
                        _.each(newEdgeIds, function(edgeId) { elesToAdd.push({group: "edges", data: cyEdgeData(updatedEdgesById[edgeId])}) });

                        var animateGraph = false;
                        if (_.size(edgesToRemove) > 0) {
                            animatedRemoveElements(cy.collection(edgesToRemove));
                            animateGraph = true;
                        }
                        if (_.size(nodesToRemove) > 0) {
                            animatedRemoveElements(
                                cy.collection(nodesToRemove),
                                function() { cy.$('#' + lastSelectedNodeId).removed() ? scope.$root.$broadcast('dt-graph-node-unselected') : null},
                                true
                            );
                            animateGraph = true;
                        }
                        if (_.size(elesToAdd) > 0) {
                            cy.add(elesToAdd);
                            animateGraph = true;
                        }
                        if (animateGraph) {
                            cy.layout(layoutOptions[scope.layout]);
                        }
                    });

                    scope.$on('dt-graph-remove-node', function(evt, node) {
                        animatedRemoveElements(cy.elements('#' + nodeId(node)), null, true);
                        cy.layout(layoutOptions[scope.layout]);
                    });

                    scope.$on('dt-graph-reset-layout', function(evt, layout) {
                        scope.layout = layout;
                        cy.layout(layoutOptions[scope.layout]);
                    });

                    window.cy = cy;

                }, 10);
            }
        }
    }])
;
