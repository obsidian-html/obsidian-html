// Keybindings
// ----------------------------------------------------------------------------

var OBSHTML_KEYPRESS_FUNCTIONS = []
document.addEventListener('keypress', HandleKeyPress);
function HandleKeyPress(e) {
    // to add a function callback on a keypress just call `OBSHTML_KEYPRESS_FUNCTIONS.push(my_func)`
    OBSHTML_KEYPRESS_FUNCTIONS.forEach(func => {
        func(e)
    })
}
document.addEventListener('DOMContentLoaded', load_theme);




// Functions 
// ----------------------------------------------------------------------------

function httpGetAsync(theUrl, callback, level, callbackpath) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp, level, theUrl, callbackpath);
    }
    xmlHttp.open("GET", theUrl, true); // true for asynchronous 
    xmlHttp.send(null);
}


// Helper Functions 
// ----------------------------------------------------------------------------

function rem(rem) {
    return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}
function vh() {
    return Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0)
}
function print(...vals){ console.log(...vals)}

function toggle(id, display_value) {
    el = document.getElementById(id);
    return toggle_el(el, display_value);
}

function toggle_el(el, display_value) {
    if (el.style.display == 'none') {
        el.style.display = display_value;
        return true
    }
    else if (el.style.display == display_value) {
        el.style.display = 'none';
        return false
    }
    else {
        el.style.display = display_value;
        return true
    }
}


function disable(id){
    disable_el(document.getElementById(id));
}
function disable_el(el){
    el.style.display = 'none';
}

function cl_toggle(id, class_name) {
    let el = document.getElementById(id);
    if (el.classList.contains(class_name)) {
        el.classList.remove(class_name)
    } else {
        el.classList.add(class_name)
    }
}

function fold_callout(el) {
    let div = el.parentElement
    if (div.classList.contains("active")) {
        div.classList.remove("active")
    } else {
        div.classList.add("active")
    }
}

// general option, to replace function above
function fold(el) {
    if (el.classList.contains("fold-active")) {
        el.classList.remove("fold-active")
    } else {
        el.classList.add("fold-active")
    }
}


function load_theme() {
    let theme_name = window.localStorage.getItem('theme_name');
    if (!theme_name){
        window.localStorage.setItem('theme_name', 'obs-light');
    }
    set_theme(window.localStorage.getItem('theme_name'));
    document.getElementById('antiflash').style.display = 'none'; 
}

function set_theme(theme_name){
    let body = document.body;

    // update localstorage 
    window.localStorage.setItem('theme_name', theme_name);

    // update select element
    document.getElementById('theme').value = theme_name;

    let theme_class = 'theme-'+theme_name;

    // remove previous theme class
    body.classList.forEach(class_name => {
        if (class_name.startsWith('theme-')){
            body.classList.remove(class_name);
        }
    });

    // add new
    body.classList.add(theme_class);
}

function toggle_menu(){
    let res = toggle('navbar', 'flex')
    let h2 = document.getElementById('header2')

    if (!res){
        disable('theme-popup');

        if (h2){
            let pu = document.getElementById('header2').getElementsByClassName('popup')[0];
            disable_el(pu);
        }
    }

    if (h2){
        let res = toggle('navbar2', 'flex');
    }
}