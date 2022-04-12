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
    //alert(args)
    var container = document.getElementById(args.result_div_id)

    if (args.code == null){
        code = 500
    } else {
        code = args.code
    }
    container.innerHTML = '<span class="code-' + code + '">' + args.message + '</span>'
    container.style.display = 'block'
}