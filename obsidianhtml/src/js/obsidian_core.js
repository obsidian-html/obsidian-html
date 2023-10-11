// Init
// ----------------------------------------------------------------------------
// Globals (filled in by backend)
var no_tab_mode = {no_tabs};
var mermaid_enabled = {mermaid_enabled};
var toc_pane_div = "{toc_pane_div}";
var dir_index_pane_div = "{dir_index_pane_div}";
var html_url_prefix = "{html_url_prefix}";
var CONFIGURED_HTML_URL_PREFIX = "{configured_html_url_prefix}";
var CONFIG_ONLY_SHOW_FOR_MULTIPLE_HEADERS = {only_show_for_multiple_headers};
var CONFIG_CLOSE_RIGHT_PANE_IF_EMPTY = {close_right_pane_if_empty};
var CONFIG_CLOSE_LEFT_PANE_IF_EMPTY = {close_left_pane_if_empty};
var RELATIVE_PATHS = {relative_paths};
var documentation_mode = {documentation_mode};
var tab_mode = !no_tab_mode;
var gzip_hash = '{gzip_hash}'                       // used to check whether the localStorage data is stale

// global cache
var fn_cache_ls_available = null;


// Onloads
// ----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', load_theme);  //set theme as quickly as possible to avoid flickering
document.addEventListener('DOMContentLoaded', load_page);   // all the code that needs to be run when everything is loaded
if (RELATIVE_PATHS){
    document.addEventListener('DOMContentLoaded', set_rel_paths);
}

function set_rel_paths(){
    // update directory navigation links
    list = document.getElementById('left_pane_content').getElementsByTagName('a')
    for (let el of list) {
        let href = el.getAttribute('href');

        if (href){
            if (PAGE_DEPTH == 0){
                el.setAttribute('href', ('.' + href));
            }
            else {
                href = href.substring(1)
                el.setAttribute('href', ('../'.repeat(PAGE_DEPTH)) + href);
            }
        }
    }
    // update directory navigation buttons
    list = document.getElementById('left_pane_content').getElementsByTagName('button')
    for (let el of list) {
        let href = el.getAttribute('href');
        if (href){
            if (PAGE_DEPTH == 0){
                el.setAttribute('href', ('.' + href));
            }
            else {
                href = href.substring(1)
                el.setAttribute('href', ('../'.repeat(PAGE_DEPTH)) + href);
            }
        }
    }
    // update navbar links
    list = document.getElementsByClassName('navbar-link')
    for (let el of list) {
        let href = el.getAttribute('href');
        if (href){
            if (href.startsWith(CONFIGURED_HTML_URL_PREFIX + '/')){
                href = href.replace(CONFIGURED_HTML_URL_PREFIX + '/', '');
            } 
            else {
                href = href.substring(1)
            }
            el.setAttribute('href', ('../'.repeat(PAGE_DEPTH)) + href);
        }
    }
}


// Keybindings
// ----------------------------------------------------------------------------

// to add a function callback on a keypress just run `OBSHTML_KEYPRESS_FUNCTIONS.push(my_func)`
var OBSHTML_KEYPRESS_FUNCTIONS = []
document.addEventListener('keypress', HandleKeyPress);
function HandleKeyPress(e) {
    OBSHTML_KEYPRESS_FUNCTIONS.forEach(func => {
        func(e)
    })
}


// Orchestration functions
// ----------------------------------------------------------------------------

function load_theme() {
    let theme_div = document.getElementById('theme');
    if (!theme_div){
        // if the theme selection div is not present, assume that the template does not support theming
        disable_antiflash();
        return false
    }

    let theme_name = ls_get('theme_name');

    if (!theme_name){
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            ls_set('theme_name', 'obs-dark');
          } else {
           
            ls_set('theme_name', 'obs-light');
          }
    }
    set_theme(ls_get('theme_name'));
    disable_antiflash();
}

function disable_antiflash() {
    if (document.getElementById('antiflash')){
        document.getElementById('antiflash').style.display = 'none'; 
    }
}

function set_theme(theme_name){
    let theme_div = document.getElementById('theme');
    if (!theme_div){
        // if the theme selection div is not present, assume that the template does not support theming
        return false
    }

    let body = document.body;

    // update localstorage 
    ls_set('theme_name', theme_name);

    // update select element
    theme_div.value = theme_name
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

function getParentContainer(el){
    parent = el.parentElement;
    while (!parent.classList.contains('container')){
        parent = parent.parentElement;
    }
    return parent
}

function load_page() {
    // let page know that js is enabled
    // ----------------------------------------------------------------------------
    signal_js_enabled(document.body)


    // Continuous observers
    // ----------------------------------------------------------------------------
    const resize_ob = new ResizeObserver(function(entries) {
        // resize the container height every time the header height changes
        let containers = document.querySelectorAll(".container");
        containers.forEach(container => {
            setContentHeight(container);
        });
    });
    resize_ob.observe(document.getElementById('header'));


    // Custom hooks and loads
    // ----------------------------------------------------------------------------
    let collection = document.getElementsByClassName("container")
    if (collection.length > 0) {
        LoadTableOfContents(collection[0])
    }

    if (tab_mode) {
        SetLinks(0);
    }
    else if (typeof DO_NOT_OVERWRITE_LINK_BEHAVIOR == 'undefined' || !DO_NOT_OVERWRITE_LINK_BEHAVIOR) {
        var links = document.getElementsByTagName('a');
        for (let i = 0; i < links.length; i++) {
            let l = links[i];
            if (l.getAttribute("href").includes('#')) {
                l.onclick = function () {
                    // remove current url from the link
                    let current_url = document.URL
                    current_url = decodeURI(current_url.replace(window.location.protocol + '//', '').replace(window.location.host, ''))
                    current_url = current_url.split('#')[0];

                    let link = decodeURI(this.getAttribute("href"))
                    link = link.replace(current_url, '')

                    // if we are left with something like: '#blabla' then we have an anchor link
                    // otherwise, we just go to the page:
                    if (link[0] != '#') {
                        link = this.getAttribute("href").replace('#', '#!')
                        window.location.href = link;
                        return false;
                    }
                    
                    // we scroll to the anchor
                    // we do this manually because scrolling divs suck
                    let levelcont = document.getElementsByClassName("container")[0];
                    let header = document.getElementById("header")
                    var el = levelcont.querySelectorAll(link.replaceAll(':', '\\:'))[0];
                    if (el) {
                        getParentContainer(el).scrollTop = el.offsetTop - (rem(1) + header.getBoundingClientRect().height) 
                        el.classList.add('fade-it');
                        setTimeout(function() {
                            el.classList.remove('fade-it');
                         }, 2000);
                    }
                    return false;
                };
                continue
            }

        }
    }

    // scroll to div
    if (window.location.hash.length > 2 && window.location.hash[1] == '!') {
        let link = '#' + window.location.hash.substring(2, window.location.hash.length)
        let levelcont = document.getElementsByClassName("container")[0].getElementsByClassName('content')[0];
        var el = levelcont.querySelectorAll(link)[0];
        if (el) {
            el.parentElement.parentElement.scrollTop = el.offsetTop - rem(6);
        }
    }


    // Scroll container to #header link
    if (tab_mode && window.location.hash != '') {
        let el = document.getElementById(window.location.hash.substr(2));
        if (el) {
            el.parentElement.parentElement.scrollTop = el.offsetTop - rem(6);
        }
    }

    // Init starting container
    FirstContainer = document.getElementsByClassName('container')[0];
    if (FirstContainer){
        FirstContainer.id = 'level-0';
        FirstContainer.level = '0';
        SetContainer(FirstContainer);
    }

    // also init side panes if present
    SetSidePanes();

    // Open the path on loading the page
    // This is everything after ?path=
    if (tab_mode) {
        let path_to_open = ''
        var href = window.location.href;
        if (href.includes('?path=')) {
            path_to_open = href.split('?path=')[1].split('/');
            for (let i = 0; i < path_to_open.length; i++) {
                path_to_open[i] = decodeURIComponent(path_to_open[i]);
            }
        }
        OpenPath(1, path_to_open);
    }
}

function LoadTableOfContents(container_div)
{
    let collection = container_div.getElementsByClassName('toc')
    if (collection.length > 0) {
        let toc = collection[0];
        if (!CONFIG_ONLY_SHOW_FOR_MULTIPLE_HEADERS || toc.getElementsByTagName('li').length > 1) {

            if (toc_pane_div && no_tab_mode) {
                let tpd = document.getElementById(toc_pane_div);
                tpd.display = 'block';
                tpd.innerHTML = '<span class="toc-header">Table of contents</span>' + '<div class="toc-contents">' + collection[0].innerHTML + '</div>';
                toc.remove();
            }
            else {
                toc.style.display = 'block';
                toc.innerHTML = '<h3>Table of Contents</h1>\n' + toc.innerHTML
            }
        }
        else{
            toc.remove();
        }
    }

}

function SetSidePanes() {
    let lp = document.getElementById('left_pane');
    let lpc = document.getElementById('left_pane_content');
    if (lp){
        if (CONFIG_CLOSE_LEFT_PANE_IF_EMPTY){
            CloseSidePaneIfEmpty(lp, lpc);
        }
    }
    if (lpc){
        SetContainer(lpc)
    }

    let rp = document.getElementById('right_pane');
    let rpc = document.getElementById('right_pane_content');
    if (rp){
        if (CONFIG_CLOSE_RIGHT_PANE_IF_EMPTY){
            CloseSidePaneIfEmpty(rp, rpc);
        }
    }
    if (rpc){
        SetContainer(rpc)
    }
}

function CloseSidePaneIfEmpty(pane_div, pane_content_div) {
    if (!pane_content_div){
        pane_div.classList.remove("active");
    } 
    if (pane_content_div && pane_content_div.innerHTML.trim() == ""){
        pane_div.classList.remove("active");
    }
}

function SetContainer(container) {
    // This function is called on every (newly created) container. 
    // One container holds one tab

    // Set url
    // This will be set already if this is not the first tab
    if (typeof container.url === 'undefined') {
        container.url = window.location.pathname;
    }

    // Set click to get header link
    SetHeaders(container);

    // wrap images in links so we can easily open the actual size (unless it is already wrapped by a link)
    wrap_imgs_with_links(container);

    // Load mermaid code
    // if (mermaid_enabled){
    //     mermaid.init()
    // }

    // callout divs are created with class 'active' to have them folded open by default
    // when js is enabled (in this case) this class is removed so the callouts are folded closed until clicked on
    // new divs are distinguished from old ones by rasa="1"/rasa="0" resp.
    let callout_folded = container.querySelectorAll(".callout-folded");
    callout_folded.forEach(div => {
        let rasa = div.getAttribute('rasa')
        if (rasa == '1'){
            div.setAttribute('rasa', 0)
            div.classList.remove('active')
        }
    });

    // requires_js can be set on elements that need to be hidden unless js is enabled
    // this block will remove the requires_js class from all elements
    signal_js_enabled(container)

    // adjust container height so content does not fall off screen
    setContentHeight(container)

    // set graph svg and button to have unique id across tabs
    let graph_div = container.querySelectorAll(".graph_div");
    if (graph_div.length == 1) {
        graph_div[0].id = graph_div[0].id.replace('{level}', container.level)
    }

    let graph_show_button = container.querySelectorAll(".graph_show_button");
    if (graph_show_button.length == 1) {
        graph_show_button[0].setAttribute('level', container.level);
        graph_show_button[0].id = graph_show_button[0].id.replace('{level}', container.level)
    }
    
    let graph_type_button = container.querySelectorAll(".graph_type_button");
    if (graph_type_button.length == 1) {
        graph_type_button[0].id = graph_type_button[0].id.replace('{level}', container.level)
    }

    let graph_instructions = container.querySelectorAll(".graph-instructions");
    if (graph_instructions.length == 1) {
        graph_instructions[0].id = graph_instructions[0].id.replace('{level}', container.level)
    }

    style_checklist(container);

    if (window.ObsHtmlGraph){
        window.ObsHtmlGraph.arm_page(container)
    }
}

// Adds link icon to headers and creates the anchor link to the header.
function SetHeaders(container) {
    let content = container.getElementsByClassName('content')
    let els = container.childNodes;
    if (content.length > 0){
        content = content[0]
        els = content.childNodes;
    }
    for (let i = 0; i < els.length; i++) {
        // Only apply this code block to h1, h2, etc
        if (typeof els[i].tagName === 'undefined' || els[i].tagName[0] != 'H' || els[i].tagName == 'HR' ) {
            continue;
        }

        // iterate
        let n = 1;

        // Test if page is open already in another tab
        anchor_id = els[i].id + '-anchor';
        if (document.getElementById(anchor_id)) {
            let loop = true;
            while (loop) {
                if (document.getElementById(anchor_id + '_' + n)) {
                    n++;
                }
                else {
                    break;
                }
            }
            anchor_id += '_' + n;
        }

        els[i].anchor_id = anchor_id;

        // Add link icon + a href to the header
        let href = window.location.origin + container.url + '#!' + els[i].id;
        els[i].innerHTML = '<a id="' + anchor_id + '" class="anchor" href="' + href + '"><svg class="octicon octicon-link" viewBox="0 0 16 16" version="1.1" width="16" height="16" aria-hidden="true"><path fill-rule="evenodd" d="M7.775 3.275a.75.75 0 001.06 1.06l1.25-1.25a2 2 0 112.83 2.83l-2.5 2.5a2 2 0 01-2.83 0 .75.75 0 00-1.06 1.06 3.5 3.5 0 004.95 0l2.5-2.5a3.5 3.5 0 00-4.95-4.95l-1.25 1.25zm-4.69 9.64a2 2 0 010-2.83l2.5-2.5a2 2 0 012.83 0 .75.75 0 001.06-1.06 3.5 3.5 0 00-4.95 0l-2.5 2.5a3.5 3.5 0 004.95 4.95l1.25-1.25a.75.75 0 00-1.06-1.06l-1.25 1.25a2 2 0 01-2.83 0z"></path></svg></a>\n' + els[i].innerHTML

        // body onload is not called when staying within the page
        // we need to call the load_page() function manually
        let href_el = document.getElementById(anchor_id);
        href_el.onclick = function () {
            window.location.replace(this.href);
            load_page(0);
        }

        // Show/hide link icon
        els[i].onmouseover = function () {
            document.getElementById(this.anchor_id).style.visibility = 'visible';
        };
        els[i].onmouseleave = function () {
            document.getElementById(this.anchor_id).style.visibility = 'hidden';
        };
    }
}

// this function is called when the user clicks on the menu button (mobile mode)
function toggle_menu(){
    // In tabs mode there will be a hidden header that needs to follow what the main header does
    // (html hack for having a fixed header and correct vertical scrolling...)
    let h2 = document.getElementById('header2')

    
    let res = toggle_id('navbar')
    if (!res){
        // If the menu is turned off --> also close the theme selector
        disable_theme_popup()
    }

    if (h2){
        // Also toggle the mirror header (tabs mode only)
        let res = toggle_id('navbar2');
    }
}

// Core Functions 
// ----------------------------------------------------------------------------
function ls_test_available(){
    if (fn_cache_ls_available != null){
        return fn_cache_ls_available
    }
    try {
        window.localStorage.setItem('obsdianhtml_test_val', 'obsdianhtml_test_val');
        window.localStorage.removeItem('obsdianhtml_test_val');
        fn_cache_ls_available = true; return true;
    } catch(e) {
        fn_cache_ls_available = false; return false;
    }
}

function ls_get(key){
    if(ls_test_available() == false){ return false }
    return window.localStorage.getItem(key);
}
function ls_set(key, value){
    if(ls_test_available() == false){ return false }
    return window.localStorage.setItem(key, value);
}


function httpGetAsync(theUrl, callback, level, callbackpath) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp, level, theUrl, callbackpath);
    }
    xmlHttp.open("GET", theUrl, true); // true for asynchronous 
    xmlHttp.send(null);
}


function load_script_on_demand(path, callback, callback_args){
    console.log('loading', path);
    // create script tag
    var elScript = document.createElement('script');
    elScript.setAttribute('type','text/javascript');
    elScript.setAttribute('charset', 'utf-8');

    // set path to load, and callback to be run when loaded
    elScript.setAttribute( 'src', path);
    elScript.addEventListener('load', (event) => {
        callback(...callback_args);
    });

    // add script tag to the end of body
    document.getElementsByTagName("body")[0].appendChild( elScript );
}

function get_graph_data(){
    if (RELATIVE_PATHS){
        let page_depth = window.location.pathname.split('/').length - CONFIGURED_HTML_URL_PREFIX.split('/').length - 1;
        if (page_depth > 0){
            return '../'.repeat(page_depth) + '/obs.html/data/graph.json';
        }
        else {
            return './' + '/obs.html/data/graph.json';
        }
    }
    return get_html_url_prefix()+'/obs.html/data/graph.json';
}
function get_html_url_prefix(){
    return '{html_url_prefix}'  // this value is replaced by the actual url prefix when compiled
}

function signal_js_enabled(container){
    let divs = container.querySelectorAll(".requires_js");
    divs.forEach(div => {
        div.classList.remove('requires_js')
    });
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


function disable_id(id){
    disable(document.getElementById(id));
}
function disable(el){
    if (el.classList.contains('active')) {
        el.classList.remove('active')
    }
}

function setContentHeight(container){
    const height = document.getElementById('header').offsetHeight;
    container.style.height = `calc(100vh - ${height}px - 2rem)`;
}

// standard
function cl_toggle_id(id, class_name){
    return cl_toggle(document.getElementById(id), class_name)
}
function cl_toggle(el, class_name) {
    if (el.classList.contains(class_name)) {
        el.classList.remove(class_name)
        return false
    } else {
        el.classList.add(class_name)
        return true
    }
}

function toggle_id(id){
    return toggle(document.getElementById(id))
}
function toggle(el){
    return cl_toggle(el, 'active')
}


function toggle_callout(el){
    cl_toggle(el, 'active')
    cl_toggle(el, 'inactive')
}

function style_checklist(element){
    let li_items = element.querySelectorAll("li");
    for (let i=0; i<li_items.length;i++){
        let li = li_items[i];

        // apply on subitems, otherwise these may be overwritten
        let sub_li_items = li.querySelectorAll("li");
        if (sub_li_items.length > 0){
            style_checklist(li);
        }

        // style list
        if (li.innerHTML.slice(0, 3) == "[ ]"){
            li.innerHTML = li.innerHTML.replace("[ ]", '<div class="unchecked">⬜</div>');
            li.classList.add("checklist-item");
        }
        else if (li.innerHTML.slice(0, 3) == "[x]"){
            li.innerHTML = li.innerHTML.replace("[x]", '<div class="checked">✔</div>');
            li.classList.add("checklist-item");
        }
    }
}

function isPartOfLink(element) {
	// Check if any parent element is a link
	let parentElement = element.parentElement;
	while (parentElement !== null) {
	  if (parentElement.tagName === 'A') {
		return true;
	  }
	  parentElement = parentElement.parentElement;
	}
  
	// If no link element found, return false
	return false;
}

function wrap_imgs_with_links(container) {
	[...container.getElementsByTagName("img")].forEach(img => {
		// don't wrap if image already is wrapped in a link
		if (isPartOfLink(img)){ return; }

		// create link wrapper
		let wrapper = document.createElement('a');
		wrapper.setAttribute('href',img.src);
		wrapper.setAttribute("target", "_blank");
		
		// put img in link
		img.parentNode.insertBefore(wrapper, img);
		wrapper.appendChild(img);
	});
}

