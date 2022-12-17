// This function is called by obshtml when it wants to open the graph
function run(args) {
    if (window.ObsHtmlGraph.graph_dependencies_loaded['2d'] == false){
        // load three dependencies in succession and then run initGraph(args)
        load_script_on_demand(
            '//unpkg.com/force-graph', load_script_on_demand, ["//unpkg.com/d3-force", load_script_on_demand, ["https://d3js.org/d3.v4.min.js", initGraph, [args]]]
        )
        // tell obshtml that the dependencies have been loaded
        window.ObsHtmlGraph.graph_dependencies_loaded['2d'] = true;

    }
    else {
        // just run directly
        initGraph(args)
    }
}

function initGraph(args) {
    // open div right before loading the graph to avoid opening an empty div
    args.graph_container.style.display = "block";

    // Load data then start graph
    fetch(args.data).then(res => res.json()).then(data => {

        // overwrites
        let g = window.ObsHtmlGraph.graphs[args.uid];
        g.actions['select_node'] = function(args, graph){
            return graph_select_node(args, graph)
        }

        g.graph = ForceGraph()
            (args.graph_container)
            .graphData(data)
            .width(args.width)
            .maxZoom(10)
            .height(args.height)
            .backgroundColor(g.colors.bg)
            .nodeLabel('name')
            .d3Force("charge", d3.forceManyBody().strength(args.coalesce_force))
            .nodeColor((node) => {return g.colors.node_inactive})
            .nodeCanvasObjectMode(() => 'after')
            .nodeCanvasObject((node, ctx, globalScale) => {
                // draw text only for nodes connected to the current node
                let isConnected = false;
                node.links.forEach(link => {
                    if (link == g.current_node_id){
                        isConnected = true;
                    }
                })
                // draw text
                if (isConnected){
                    const label = node.name;
                    const fontSize = 11 / globalScale;
                    ctx.font = `${fontSize}px Sans-Serif`;
                    const textWidth = ctx.measureText(label).width;                
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = g.colors.text;
                    ctx.fillText(label, node.x, node.y+8);
                }
                
                // color only main node & semiconnected
                if (node.id != g.current_node_id){
                    if (isConnected){
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, 4, 0, 2 * Math.PI);
                        ctx.fillStyle = g.colors.node_semiactive;
                        ctx.fill();
                    }
                    return
                }

                // color node
                ctx.beginPath();
                ctx.arc(node.x, node.y, 4+1, 0, 2 * Math.PI);
                ctx.fillStyle = g.colors.node_active_border;
                ctx.fill();
                ctx.beginPath();
                ctx.arc(node.x, node.y, 4, 0, 2 * Math.PI);
                ctx.fillStyle = g.colors.node_active;
                ctx.fill();

            })
            .linkColor(link => {
                if (link.source.id == g.current_node_id){
                    return g.colors.link_active
                }
                if (link.target.id == g.current_node_id){
                    return g.colors.link_active
                }
                return g.colors.link_inactive
            })
            .linkDirectionalParticles("value")
            .linkDirectionalParticleSpeed(0.010)
            .linkDirectionalParticleWidth(link => {
                if (link.source.id == g.current_node_id || link.target.id == g.current_node_id){
                    return 4.0
                }
                return 0
            })
            // [425] Add included references as links in graph view
            .linkLineDash(link => {
                if (link.type == 'inclusion'){
                    return [1,1]
                }
                return false;
            })
            .onNodeClick(node => {
                args.node = node;
                g.actions['left_click'](args)
            })
            .onNodeRightClick(node => {
                args.node = node;
                g.current_node_id = node.id
                g.actions['right_click'](args)
            })
        
        setTimeout( () => g.graph.zoomToFit(1000, rem(3), function(n){return zoom_select(n, args)}), 1000 );
    });
}

// HELPER FUNCTIONS
/////////////////////////////////////////////////////////////////////////////////////

function graph_select_node(args){
    let g = window.ObsHtmlGraph.graphs[args.uid];
    g.current_node_id = args.node.id;

    g.graph.zoomToFit(1000, rem(3), function(n){return zoom_select(n, args)})
    return false;
}

function zoom_select(n, args){
    let g = window.ObsHtmlGraph.graphs[args.uid];
    if (g == undefined){ // graph closed before settimeout got around to zooming
        return false
    }

    if (n.id == g.current_node_id){
        return true
    }
    for (let i=0;i<n.links.length;i++){
        if (n.links[i] == g.current_node_id){
            return true
        }
    }
    return false
}

/////////////////////////////////////////////////////////////////////////////////////

// export the run() method so that it can be called by obshtml
export { 
    run
};