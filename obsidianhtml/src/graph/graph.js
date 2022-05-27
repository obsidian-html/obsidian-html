import * as grapher_2d from '{html_url_prefix}/obs.html/static/default_grapher_2d.js';
import * as grapher_3d from '{html_url_prefix}/obs.html/static/default_grapher_3d.js';

// INFORMATION
//////////////////////////////////////////////////////////////////////////////
// These help in avoiding reloading dependencies when they are already loaded
var graph_dependencies_loaded = {}
graph_dependencies_loaded['2d'] = false;
graph_dependencies_loaded['3d'] = false;

// Set functions to be called via a hashtable so that we can overwrite certain functions per graph type
var default_actions = {
    'left_click': graph_left_click,
    'right_click': graph_right_click,
    'open_link': graph_open_link,
    'select_node': graph_select_node
}

var default_colors = {
    'bg': 'var(--graph-bg)',    // only color where var value is allowed
    'node_inactive': '#909099',
    'node_active': '#7f6df2',
    'node_semiactive': '#c6bff7',
    'node_active_border': '#dcddde',
    'link_active': '#7f6df2',
    'link_inactive': '#2e2e2e',
    'text': '#dcddde'
}

// Graph listing mutations
//////////////////////////////////////////////////////////////////////////////
var graphs = {};                                // each graph has an object in this hashtable. see new_graph_listing() for type

function new_graph_listing(){
    return {
        'current_node_id': '',                  // the currently selected node
        'pinned_node': '',                      // the node that this graph belongs to
        'graph': null,                          // the actual graph object responsible for showing the graph
        'active': false,                        // whether the graph is currently loaded and visible
        'type_d': '',                           // e.g. '2D'
        'container': null,                      // the div that contains the graph
        'width': 0,                             // width of the container in px
        'height': 0,                            // height of the container in px
        'actions': clone(default_actions),      // what functions to call based on which actions
        'colors': clone(default_colors)
    }
}

function add_graph(uid, pinned_node, type_d, container){
    graphs[uid] = new_graph_listing()
    graphs[uid]['current_node_id'] = pinned_node
    graphs[uid]['pinned_node'] = pinned_node
    graphs[uid]['type_d'] = type_d
    graphs[uid]['container'] = container

    // to set width and height we need to momentarily ensure that the div is visible
    let original = container.style.display
    container.style.display = "block"

    graphs[uid]['width']  = container.clientWidth;
    graphs[uid]['height'] = container.clientHeight;

    container.style.display = original;
}
function remove_graph(uid, cont, close){
    cont.innerHTML = "";
    
    if (close){
        delete graphs[uid];
    } else {
        graphs[uid].actions = clone(default_actions);
        graphs[uid].colors  = clone(default_colors)
    }
}

// Initialisation
//////////////////////////////////////////////////////////////////////////////
function run(button, ntid, pinned_node)
{
    // Get elements
    let level = button.getAttribute('level');
    let uid = ntid + level

    let cont = document.getElementById('A'+uid);
    let type_button = document.getElementById('C'+uid);
    
    let type_d = type_button.innerHTML.trim();

    // add new graph listing if not yet exists
    // this listing allows us to keep track of data related to the specific graph on the "backend"
    if (uid in graphs == false){
        add_graph(uid, pinned_node, type_d, cont)
    }

    // toggle graph on or off
    if (button.innerHTML == 'Hide Graph'){
        button.innerHTML = 'Show Graph';
        cont.style.display = "none";
        remove_graph(uid, cont, true);
        return;
    }
    else {
        button.innerHTML = "Hide Graph";
    }

    // Init graph
    if (!graphs[uid].active){
        enable_graph(uid)
    } 
}

function enable_graph(uid){
    let args = get_graph_args(uid)

    args.current_node_id = graphs[uid].current_node_id
    
    if (graphs[uid].type_d == '2D'){
        grapher_2d.run(args)
    }
    else if (graphs[uid].type_d == '3D'){
        grapher_3d.run(args)
    }

    graphs[uid].active = true;
    graph_dependencies_loaded[graphs[uid].type_d] = true
}

// the args hashtable is sent to the grapher function to tell it what it needs to know to draw the graph
function get_graph_args(uid){
        let cont = document.getElementById('A'+uid);
        let data = get_graph_data();

        let original = cont.style.display
        cont.style.display = "block"
        let width = cont.clientWidth;
        let height = cont.clientHeight;
        cont.style.display = original;

        let args = {
                'uid': uid,
                'graph_container': cont, 
                'width': width, 
                'height': height, 
                'data': data, 
                'node': null, 
                'link': null,
                'coalesce_force': '{coalesce_force}'
            }
        return args
}

// OVERWRITABLE ACTIONS
//////////////////////////////////////////////////////////////////////////////
function graph_left_click(args){
        return act(args, 'open_link')(args)()
}

function graph_right_click(args){
        //return graph_select_node(args, graph)
        return act(args, 'select_node')(args)
}

// LEAF ACTIONS
// fn
function graph_open_link(args){
    if (! {no_tabs})
    {
        return graph_open_link_tabs(args)
    }
    else {
        return graph_open_link_normal(args)
    }
}

// fn
function graph_open_link_tabs(args){
    let url = args.node.url;

    return function() {
        let level = parseInt(args.graph_container.parentElement.parentElement.level);
        httpGetAsync(encodeURI(url), ReceiveCall, level+1, false); 
        return false;
    }
}

// fn
function graph_open_link_normal(args){
    let url = args.node.url;

    return function(){
        window.location.href = url;
        return false;
    }
}
// (action)
function graph_select_node(args){
    graphs[args.uid].current_node_id = args.node.id;
    graphs[args.uid].graph.refresh();
    return false;
}

// HELPER FUNCTIONS
//////////////////////////////////////////////////////////////////////////////

function act(args, action_name){
    return graphs[args.uid].actions[action_name]
}

function switch_graph_type(button){
    // toggle button
    _toggle_graph_type_button(button);

    // get type_d
    let type_d = button.innerHTML.trim();
    window.localStorage.setItem('graph_type_d', type_d);

    // get stuff
    let uid = button.id.substring(1);
    let g = window.ObsHtmlGraph.graphs[uid];
    let cont = document.getElementById('A'+uid);

    // exit if g does not exist (graph not open atm)
    if (g == undefined){
        return
    }

    // switch out graph if active
    if (g.active){
        cont.style.display = "none";
        remove_graph(uid, cont, false);

        graphs[uid].type_d = type_d

        enable_graph(uid);
    }

}
function _toggle_graph_type_button(button){
    // set button to show other text
    if (button.innerHTML.trim() == '2D'){
        button.innerHTML = '3D'
    }
    else {
        button.innerHTML = '2D'
    }
}

function test(){
    console.log('bla')
}

function clone(obj) {
    var copy;

    // Handle the 3 simple types, and null or undefined
    if (null == obj || "object" != typeof obj) return obj;

    // Handle Object
    if (obj instanceof Object) {
        copy = {};
        for (var attr in obj) {
            if (obj.hasOwnProperty(attr)) copy[attr] = clone(obj[attr]);
        }
        return copy;
    }

    throw new Error("Unable to copy obj! Its type isn't supported.");
}


export { 
    test,
    switch_graph_type,
    run, 
    graphs, 
    graph_dependencies_loaded, 
    default_actions,
    graph_select_node,
    graph_open_link_normal,
    graph_open_link
};