function run(args) {
    function start(){
        args.graph_container.style.display = "block";       // open div right before loading the graph to avoid opening an empty div
        initGraph_3d(args)
        window.ObsHtmlGraph.graph_dependencies_loaded['3d'] = true;
    }

    if (window.ObsHtmlGraph.graph_dependencies_loaded['3d'] == false){
        load_script_on_demand(
            CONFIGURED_HTML_URL_PREFIX + '/obs.html/static/3d-force-graph.js', 
            start,
            []
        )
    }
    else {
        start();
    }
}

function initGraph_3d(args) {
    let g = window.ObsHtmlGraph.graphs[args.uid];
    g.graph = ForceGraph3D()
        (args.graph_container)
        .jsonUrl(args.data)
        .width(args.width)
        .height(args.height)
        .nodeLabel('name')
        .linkDirectionalParticles("value")
        .linkDirectionalParticleSpeed(0.010)
        .linkDirectionalParticleWidth(2.0)
        .nodeColor(node => {
            if (node.id == g.current_node_id){
                return '#ff0000'
            }
            let isConnected = false;
            node.links.forEach(link => {
                if (link == g.current_node_id){
                    isConnected = true;
                }
            })
            if (isConnected){
                return '#f7be49';
            }
            return '#ffffff'
        })
        .linkColor(link => {
            if (link.source == g.current_node_id || link.target == g.current_node_id){
                return '#ff0000'
            }
            return '#dadada'
        })
        .linkOpacity(0.3)
        .onNodeClick(node => {
            args.node = node;
            g.actions['left_click'](args)
        })
        .onNodeRightClick(node => {
            args.node = node;
            g.actions['right_click'](args, g.graph)
        });
}


export { 
    run
};