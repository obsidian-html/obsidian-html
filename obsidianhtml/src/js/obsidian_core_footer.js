// Init
// ----------------------------------------------------------------------------
// Globals
var path_to_open = [];

var no_tab_mode = {no_tabs};
var toc_pane = {toc_pane};
var mermaid_enabled = {mermaid_enabled};
var toc_pane_div = "{toc_pane_div}";
var content_pane_div = "{content_pane_div}";
var html_url_prefix = "{html_url_prefix}";
var documentation_mode = {documentation_mode};
var tab_mode = !no_tab_mode;
var gzip_hash = '{gzip_hash}'

// Functions 
// ----------------------------------------------------------------------------
function LoadPage() {
    if (documentation_mode) {
        httpGetAsync(html_url_prefix + '/obs.html/data/graph.json', load_dirtree_as_left_pane, 0, 'callbackpath');
    }

    let collection = document.getElementsByClassName("container")
    if (collection.length > 0) {
        LoadTableOfContents(collection[0])
    }

    if (tab_mode) {
        SetLinks(0);
    }
    else {
        var links = document.getElementsByTagName('a');
        for (let i = 0; i < links.length; i++) {
            let l = links[i];
            if (l.getAttribute("href").includes('#')) {
                l.onclick = function () {

                    let current_url = document.URL
                    current_url = decodeURI(current_url.replace(window.location.protocol + '//', '').replace(window.location.host, ''))
                    let link = this.getAttribute("href")
                    link = link.replace(current_url, '')

                    if (link[0] != '#') {
                        link = this.getAttribute("href").replace('#', '#!')
                        window.location.href = link;
                        return false;
                    }

                    let levelcont = document.getElementsByClassName("container")[0];
                    var el = levelcont.querySelectorAll(link)[0];
                    if (el) {
                        el.parentElement.scrollTop = el.offsetTop - rem(6);
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
        let levelcont = document.getElementsByClassName("container")[0];
        var el = levelcont.querySelectorAll(link)[0];
        if (el) {
            el.parentElement.scrollTop = el.offsetTop - rem(6);
        }
    }


    // Scroll container to #header link
    if (tab_mode && window.location.hash != '') {
        let el = document.getElementById(window.location.hash.substr(2));
        if (el) {
            el.parentElement.scrollTop = el.offsetTop - rem(6);
        }
    }

    // Init starting container
    FirstContainer = document.getElementsByClassName('container')[0];
    if (FirstContainer){
        FirstContainer.id = 'level-0';
        FirstContainer.level = '0';
        SetContainer(FirstContainer);
    }

    // Open the path on loading the page
    // This is everything after ?path=
    if (tab_mode) {
        var href = window.location.href;
        if (href.includes('?path=')) {
            path_to_open = href.split('?path=')[1].split('/');
            for (let i = 0; i < path_to_open.length; i++) {
                path_to_open[i] = decodeURIComponent(path_to_open[i]);
            }
        }
        OpenPath(1);
    }
}

function LoadTableOfContents(container_div)
{
    let collection = container_div.getElementsByClassName('toc')
    if (collection.length > 0) {
        let toc = collection[0];
        if (toc.getElementsByTagName('li').length > 1) {

            if (toc_pane && no_tab_mode) {
                let tpd = document.getElementById(toc_pane_div);
                tpd.display = 'block';
                tpd.innerHTML = '<span class="toc-header">Table of contents</span>' + collection[0].innerHTML;
            }
            else {
                toc.style.display = 'block';
                toc.innerHTML = '<h3>Table of Contents</h1>\n' + toc.innerHTML
            }
        }
    }

}


// FUNCTIONS 
// ----------------------------------------------------------------------------
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

    // Load mermaid code
    if (mermaid_enabled){
        mermaid.init()
    }

    // set graph svg and button to have unique id across tabs
    svgs = container.querySelectorAll(".graph_svg");
    if (svgs.length == 1) {
        svgs[0].id = svgs[0].id.replace('{level}', container.level)
    }

    divs = container.querySelectorAll(".graph_div");
    if (divs.length == 1) {
        divs[0].id = divs[0].id.replace('{level}', container.level)
    }

    let buttons = container.querySelectorAll(".graph_button");
    if (buttons.length == 1) {
        buttons[0].level = container.level;
        buttons[0].id = buttons[0].id.replace('{level}', container.level)
    }
}

// Adds link icon to headers and creates the anchor link to the header.
function SetHeaders(container) {
    let els = container.childNodes;
    for (let i = 0; i < els.length; i++) {
        if (typeof els[i].tagName === 'undefined' || els[i].tagName[0] != 'H') {
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
        // we need to call the LoadPage() function manually
        let href_el = document.getElementById(anchor_id);
        href_el.onclick = function () {
            window.location.replace(this.href);
            LoadPage(0);
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


