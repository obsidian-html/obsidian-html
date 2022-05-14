var current_node_id = '';
var Graph = null;

function run(uid, pinnedNode)
{
    // set current node
    current_node_id = pinnedNode;

    // Get elements
    let _button = document.getElementById('B' + uid);
    let cont = document.getElementById('A'+uid);

    // toggle graph on or off
    if (_button.innerHTML == 'Hide Graph'){
        _button.innerHTML = 'Show Graph';
        cont.style.display = "None";
    }
    else {
        _button.innerHTML = "Hide Graph";
        cont.style.display = "block";
    }

    args = get_graph_args(uid)
    args.current_node_id = pinnedNode

    grapher(args)
}

function get_graph_args(uid){
        let cont = document.getElementById('A'+uid);
        let data = get_graph_data();

        let width = cont.clientWidth;
        let height = cont.clientHeight;

        let args = {
                'graph_container': cont, 
                'width': width, 
                'height': height, 
                'current_node_id':null, 
                'data': data, 
                'node': null, 
                'link': null,
                'coalesce_force': '{coalesce_force}'
            }
        return args
}

function get_graph_data(){
        return '{html_url_prefix}/obs.html/data/graph.json';
}

function get_node_graph_data(){
        return '{html_url_prefix}/obs.html/data/node_graph.json';
}


function graph_left_click(args){
        return graph_open_link(args)
}

function graph_right_click(args){
        return graph_select_node(args)
}

function graph_open_link(args){
    if (! {no_tabs})
    {
        return graph_open_link_tabs(args)
    }
    else {
        return graph_open_link_normal(args)
    }
}

function graph_open_link_tabs(args){
    let url = args.node.url;

    return function() {
        let level = parseInt(args.graph_container.parentElement.parentElement.level);
        httpGetAsync(encodeURI(url), ReceiveCall, level+1, false); 
        return false;
    }
}

function graph_open_link_normal(args){
    let url = args.node.url;

    return function(){
        window.location.href = url;
        return false;
    }
}

function graph_select_node(args){
        return function() {
            current_node_id = args.node.id;
            Graph.refresh();
            return false;
        }
}

