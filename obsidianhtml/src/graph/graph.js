// // DYNAMIC
// ///////////////////////////////////////////////////////////////////////////////
// import * as grapher_custom from '/obs.html/static/graphers/custom.js';
// import * as grapher_3d from '/obs.html/static/graphers/3d.js';
// import * as grapher_2d from '/obs.html/static/graphers/2d.js';

// var graphers = [
// 	{'id': 'custom', 'name': 'custom', 'module': grapher_custom},
// 	{'id': '3d', 'name': '3d', 'module': grapher_3d},
// 	{'id': '2d', 'name': '2d', 'module': grapher_2d}
// ]
// var graphers_hash = {
// 	'custom': {'id': 'custom', 'name': 'custom', 'module': grapher_custom},
// 	'3d': {'id': '3d', 'name': '3d', 'module': grapher_3d},
// 	'2d': {'id': '2d', 'name': '2d', 'module': grapher_2d}
// }


// INFORMATION
//////////////////////////////////////////////////////////////////////////////
// These help in avoiding reloading dependencies when they are already loaded
var graph_dependencies_loaded = {}
graphers.forEach(grapher => {
    graph_dependencies_loaded[grapher.id] = false;
});

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
    'node_semiactive': '#b6abff',
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
        'grapher_module': null,                 // the code that is responsible for creating  the graph object below. should be a module that exports a run() method.
        'graph': null,                          // the actual graph object responsible for showing the graph
        'active': false,                        // whether the graph is currently loaded and visible
        'grapher_id': '',                       // e.g. '2D'
        'container': null,                      // the div that contains the graph
        'width': 0,                             // width of the container in px
        'height': 0,                            // height of the container in px
        'actions': clone(default_actions),      // what functions to call based on which actions
        'colors': clone(default_colors)
    }
}

function add_graph(uid, pinned_node, grapher_id, container){
    graphs[uid] = new_graph_listing()
    graphs[uid]['current_node_id'] = pinned_node
    graphs[uid]['pinned_node'] = pinned_node
    graphs[uid]['grapher_id'] = grapher_id
    graphs[uid]['grapher_module'] = graphers_hash[grapher_id].module
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
function arm_page(container){
    // fetch or set default graph type values
    let grapher_name = window.localStorage.getItem('grapher_name');
    if (!grapher_name){
        window.localStorage.setItem('grapher_name', graphers[0].name);
        grapher_name = graphers[0].name;
    }

    let grapher_id = window.localStorage.getItem('grapher_id');
    if (!grapher_id){
        window.localStorage.setItem('grapher_id', graphers[0].id);
        grapher_id = graphers[0].id;
    }

    // update graph buttons that don't have a grapher_id attribute set
    let graph_type_buttons = container.querySelectorAll(".graph_type_button");
    graph_type_buttons.forEach(
        graph_type_button => 
        {
            let grapher_id_button = graph_type_button.getAttribute('grapher_id')
            if (!grapher_id_button){
                graph_type_button.setAttribute('grapher_id', grapher_id)
                graph_type_button.innerHTML = grapher_name
            }
        }
    );
}

function run(button, ntid, pinned_node)
{
    // Get elements
    let level = button.getAttribute('level');
    let uid = ntid + level

    let cont = document.getElementById('A'+uid);
    let type_button = document.getElementById('C'+uid);
    
    let grapher_id = type_button.getAttribute('grapher_id')

    // add new graph listing if not yet exists
    // this listing allows us to keep track of data related to the specific graph on the "backend"
    if (uid in graphs == false){
        add_graph(uid, pinned_node, grapher_id, cont)
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

    graphs[uid]['grapher_module'].run(args)

    graphs[uid].active = true;
    graph_dependencies_loaded[graphs[uid].grapher_id] = true
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

// UPDATE/RELOAD ACTIONS
///

// this function is called when a graph type button is clicked
function switch_graph_type(button){
    let uid = button.id.substring(1);

    // toggle button
    let grapher_listing = _toggle_graph_type_button(button);

    // update info with new grapher choice
    let graph = set_grapher(grapher_listing, uid)

    // exit if graph does not exist (graph not open atm)
    if (graph == undefined){
        return
    }

    // switch out graph if active
    if (graph.active){
        graph.container.style.display = "none";
        remove_graph(uid, graph.container, false);

        enable_graph(uid);
    }
}

function _toggle_graph_type_button(button){
    // get next list id
    let next_list_i = -1;
    let grapher_id = button.getAttribute('grapher_id')
    for(let i=0; i<graphers.length; i++){
        if (graphers[i].id == grapher_id){
            if (i < (graphers.length-1)){
                next_list_i = i+1
            } else {
                next_list_i = 0
            }
            break
        }
    }
    if (next_list_i == -1){
        console.log('ERROR: could not find list id for grapher id of "' + grapher_id + '"')
    }

    // update button
    button.setAttribute('grapher_id', graphers[next_list_i].id)
    button.innerHTML = graphers[next_list_i].name

    return graphers[next_list_i];
}
function set_grapher(grapher_listing, uid){
    // update localstorage
    // local storage keeps track of the user's latest choice for grapher, to use this as the next default
    window.localStorage.setItem('grapher_id', grapher_listing.id);
    window.localStorage.setItem('grapher_name', grapher_listing.name);

    // update button
    // button updates itself, this is skipped

    // update graph to which the button belongs
    if (uid){
        if (uid in graphs){
            graphs[uid]['grapher_module'] = graphers_hash[grapher_listing.id].module
            return graphs[uid];
        }
        return false;
    }
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
    graph_open_link,
    arm_page
};