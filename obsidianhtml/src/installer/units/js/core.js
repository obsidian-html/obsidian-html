// HTML Functions
// -----------------------------------------------------------------------
function toggle(id) {
    let cont = document.getElementById(id)
    if (cont.style.display == 'none') {
        cont.style.display = 'block'
    } else {
        cont.style.display = 'none'
    }
}

function set_form_status(done) {
    let el = document.getElementById("exit-button")
    if (el) {
        if (done) {
            el.classList.add("done");
        } else {
            el.classList.remove("done");
        }
    }
}

function span_wrap(msg, code) {
    return '<span class="code-' + code + '">' + msg + '</span>'
}

// API
// -----------------------------------------------------------------------
function api(method, args, resultdiv_id) {
    action = showResponseEnclosure(resultdiv_id)
    pywebview.api.call(method, args).then(action).catch(action)
}
function showResponseEnclosure(resultdiv_id) {
    return function(response) {
        showResponse(response, resultdiv_id)
    }
}
function showResponse(args) {
    let is_error = false;

    // The calling function should pass the result_div_id to the API function, which in turn is responsible
    // for putting it in the args variable.
    // Any terminating error will result in an args variable that only has the message attribute.
    // In this case (and when the caller doesn't set the result_div_id), put the error in the error-box
    let container = document.getElementById(args.result_div_id)
    let error_list = document.getElementById('error-list') // contains only the error itself

    if (container == null){
        is_error = true;
        container = error_list;
        showErrorBox();
    }

    // Set result code if missing. The codes follow http result code conventions.
    if (args.code == null){
        code = 500
    } else {
        code = args.code
    }

    if (code != 200){
        is_error = true;
    }

    // We always expect message to be present, as this is added even in the case of terminating errors.
    // If it is not, we are doing something wrong.
    if (args.message == null){
        alert(args)
        args.message = 'args.message was null';
        is_error = true;
    }

    // set contents of div
    let msg = '<span class="code-' + code + '">' + args.message + '</span>'
    container.innerHTML = msg;

    if (is_error){
        showErrorBox(msg);
    }

    // Make sure the container is visible
    container.style.display = 'block'

    // Tag the container as errored so it doesn't get overwritten by AutoReload
    container.is_error = is_error;

    // reload values
    AutoReload();
}


function coreOnPywebviewReady(){
    var container = document.getElementById('pywebview-status')
    container.innerHTML = '<span style="color:green">GUI initialized</span>'

    // presets
    AutoReload();
}

function coreOnClick(){
    hideErrorBox();
}

function hideErrorBox(){
    let error_container = document.getElementById('error-box');
    if (error_container.classList.contains('hidden') == false){
        error_container.classList.add('hidden');
    }
}
function showErrorBox(msg){
    let error_container = document.getElementById('error-box');
    if (error_container.classList.contains('hidden')){
        error_container.classList.remove('hidden');
    }

    // show error message if passed in
    if (msg){
        document.getElementById('error-list').innerHTML = msg;
    }
}

function AutoReload(){
    pywebview.api.read_ledger(load_list).then(handleAutoReload).catch(handleAutoReload)
}

function handleAutoReload(response) {
    for (let i = 0; i < response.data.length; i++) {
        let req = response.data[i]

        // get container to put value in
        let container = document.getElementById(req.div_id)       
        if (!container){
            showErrorBox(span_wrap('Div with id '+req.div_id+' was not found.', 500));
        }
        let val = req.value

        if (val == '') {
            val = span_wrap('Not configured', 0)
        }

        if (container.is_error == true){
            container.is_error = false
        }
        else {
            container.innerHTML = val
        }
    }
}