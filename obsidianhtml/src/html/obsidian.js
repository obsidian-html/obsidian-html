// Init
// ----------------------------------------------------------------------------
// Globals
var path_to_open = [];
var no_tab_mode = {no_tabs};
var toc_pane = {toc_pane};
var toc_pane_div = "{toc_pane_div}";
var content_pane_div = "{content_pane_div}";
var html_url_prefix = "{html_url_prefix}";
var documentation_mode = {documentation_mode};
var tab_mode = ! no_tab_mode;

function LoadPage() {
        console.log('threshold', (1.2 * 40 * getComputedStyle(document.documentElement).fontSize.split("px")[0]));

        if (documentation_mode){
                httpGetAsync(html_url_prefix+'/obs.html/data/graph.json', load_dirtree_as_left_pane, 0, 'callbackpath');
        }
        if (toc_pane && no_tab_mode){
                let collection = document.getElementsByClassName("toc");
                if (collection.length > 0){
                        let toc = collection[0];
                        toc.style.display = 'none';
                        let tpd = document.getElementById(toc_pane_div);
                        tpd.display = 'block';
                        tpd.innerHTML = '<span class="toc-header">Table of contents</span>' + collection[0].innerHTML;
                }
        }

        if (tab_mode){
                SetLinks(0);
        }
        else {
                var links = document.getElementsByTagName('a');
                for (let i = 0; i < links.length; i++) {
                        let l = links[i];
                        if (l.getAttribute("href").includes('#')){
                                l.onclick = function () {

                                        let current_url = document.URL
                                        current_url = decodeURI(current_url.replace(window.location.protocol+'//', '').replace(window.location.host, ''))
                                        let link = this.getAttribute("href")
                                        link = link.replace(current_url, '')

                                        if (link[0] != '#'){
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
        if (window.location.hash.length > 2 && window.location.hash[1] == '!'){
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
        FirstContainer.id = 'level-0';
        FirstContainer.level = '0';
        SetContainer(FirstContainer);

        // Open the path on loading the page
        // This is everything after ?path=
        if (tab_mode){
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

// Keybindings
// ----------------------------------------------------------------------------
document.addEventListener('keypress', HandleKeyPress);
function HandleKeyPress(e) {
        // Center the note of which the number was pressed
        var key = e.keyCode || e.charCode;
        if (key >= 49 && key <= 57) {
                let num = key - 48;
                console.log('You pressed ' + num);
                CenterNote(num - 1);
        }
        // move left or right
        else {
                if (key == 44) {                         // , (<)
                        ScrollNotes('left');
                }
                else if (key == 46) {                    // . (>)
                        ScrollNotes('right');
                }
        }
}

// FUNCTIONS 
// ----------------------------------------------------------------------------
// load dirtree as left-pane
function load_dirtree_as_left_pane(xmlHttp, level, theUrl, callbackpath){
        const jsonData = JSON.parse(xmlHttp.responseText);
        let cpd = document.getElementById(content_pane_div)
        let filename = ''
        let folder = ''
        // get current node
        for (let i=0; i < jsonData.nodes.length; i++){
                let node = jsonData.nodes[i];
                if (node.id == CURRENT_NODE){
                        // disable content nav if configured on the node
                        if ("obs.html" in node.metadata && "disable_dir_nav" in node.metadata['obs.html']){
                                if (node.metadata['obs.html'].disable_dir_nav){
                                        cpd.style.maxWidth = '0.7rem'
                                        cpd.style.minWidth = '0.7rem'
                                        cpd.style.padding = '0rem'
                                        return
                                }
                        }
                        folder = node.url.split('/')
                        filename = folder.pop()
                        folder = folder.join('/')

                        break;
                }
        }

        // current node not found
        if (filename == ''){
                cpd.style.maxWidth = '0.7rem'
                cpd.style.minWidth = '0.7rem'
                cpd.style.padding = '0rem'
                return
        }

        // get all links in the same folder
        let links = []
        for (let i=0; i < jsonData.nodes.length; i++){
                let node = jsonData.nodes[i];
                if (node.url.startsWith(folder) == false){
                        continue;
                }
                
                let url = node.url
                if (folder != ''){
                        url = url.replace(folder+'/', '')
                }
                if (url.includes('/')){
                        continue
                }
                if (node.url[0] != '/'){
                        node.url = '/' + node.url;
                }
                links.push({'id': node.id, 'url':node.url})
        }        

        // skip if no links found        
        if (links.length < 2){
                return
        }

        // sort list alphabetically
        function compare_lname( a, b )
        {
                if ( a.id.toLowerCase() < b.id.toLowerCase()){
                return -1;
                }
                if ( a.id.toLowerCase() > b.id.toLowerCase()){
                return 1;
                }
                return 0;
        }
      
        links.sort(compare_lname);

        let html = ''
        let header = links[0]['url'].split('/')[0]
        if (header == 'index.html'){
                header = 'Contents'
        }
        html += '<span class="toc-header">'+header+'</span><ul>'
        for (let i=0; i < links.length; i++){
                if (links[i].id == CURRENT_NODE){
                        html += '<li class="current_page_link"><a href="'+links[i].url+'">'+links[i].id+'</a></li>'
                }
                else {
                        html += '<li><a href="'+links[i].url+'">'+links[i].id+'</a></li>'
                }
        }
        html += '</ul>'
        
        cpd.innerHTML = html;
}

function rem(rem) {
        return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}

function CenterNote(level) {
        let cont = document.getElementById('level-' + level);
        let margin_left = (window.visualViewport.width - cont.getBoundingClientRect().width) / 2
        let note_left = cont.getBoundingClientRect().left
        window.scrollTo(window.visualViewport.pageLeft - (margin_left - note_left), 0)
}

function SetNoteRight(level) {
        let cont = document.getElementById('level-' + level);
        let w = parseInt(getComputedStyle(cont.parentElement).maxWidth.replace('px',''));

        let nl_target = window.visualViewport.width - w - rem(4);
        let nl = cont.getBoundingClientRect().left
        window.scrollTo(window.visualViewport.pageLeft + (nl - nl_target), 0)
}

function ScrollNotes(direction) {
        // find note that is currently in the middle
        page_center = window.visualViewport.width / 2
        max_level = FindNoteMaxLevelRecurse(0);

        let cont; let found_note = false; let level = null;
        for (let l = 0; l <= max_level; l++) {
                cont = document.getElementById('level-' + l);
                rect = cont.getBoundingClientRect();
                if (rect.left < page_center && rect.right > page_center) {
                        found_note = true;
                        level = l;
                        break
                }
        }
        // scroll to the next note
        if (direction == 'left') {
                // check to see if there is a note lower than it
                if (level == 0) {
                        return
                }
                CenterNote(level - 1)
        } else if (direction == 'right') {
                // check to see if there is a note higher than it
                if (level == max_level) { return }
                CenterNote(level + 1);
        }
        else { console.log('direction not known') }
}

function FindNoteMaxLevelRecurse(level) {
        let cont = document.getElementById('level-' + level);
        if (cont === null) {
                return (level - 1)
        }
        return FindNoteMaxLevelRecurse(level + 1)
}

function OpenPath(level) {
        if (path_to_open.length > 0) {
                let path = path_to_open.shift();
                if (path != '') {
                        httpGetAsync(path, ReceiveCall, level, true);
                }
        }
}

// Change link operation
function SetLinks(level) {
        size_of_rem = getComputedStyle(document.documentElement).fontSize.split("px")[0];
        if (window.visualViewport.width > (1.2 * 40 * size_of_rem)) {
                var links = document.getElementsByTagName('a');
                for (let i = 0; i < links.length; i++) {
                        let l = links[i];
                        if (l.className == 'anchor') {
                                continue;
                        }
                        if (l.id == 'homelink') {
                                continue;
                        }
                        if (l.classList.contains('system-link')) {
                                continue;
                        }
                        if (l.classList.contains('external-link')) {
                                continue;
                        }
                        if (l.classList.contains('navbar-link')) {
                                continue;
                        }                        

                        if (no_tab_mode && l.getAttribute("href")[0] == '#'){
                                l.onclick = function () {
                                        let levelcont = document.getElementsByClassName("container")[0];
                                        var el = levelcont.querySelectorAll("#table-of-contents")[0];
                                        if (el) {
                                                el.parentElement.scrollTop = el.offsetTop - rem(1);
                                        }
                                        return false;
                                };
                                continue
                        }
                        if (tab_mode && l.classList.contains('anchor-link')) {
                                l.onclick = function () {
                                        console.log('anch')
                                        levelcont = this.closest('div')
                                        var el = levelcont.querySelectorAll(this.getAttribute("href"))[0];
                                        if (el) {
                                                el.parentElement.scrollTop = el.offsetTop - rem(1);
                                        }
                                        return false;
                                };
                                continue
                        }
                        if (l.onclick != null) {
                                continue;
                        }
                        l.onclick = function () {
                                httpGetAsync(encodeURI(this.attributes.href.nodeValue), ReceiveCall, level + 1, false);
                                return false;
                        };
                }
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

        // Load mermaid code
        mermaid.init()

        // set graph svg and button to have unique id across tabs
        svgs = container.querySelectorAll(".graph_svg");
        if (svgs.length == 1) {
                svgs[0].id = svgs[0].id.replace('{level}', container.level)
        }

        let buttons = container.querySelectorAll(".graph_button");
        if (buttons.length == 1) {
                buttons[0].level = container.level;
                buttons[0].id = buttons[0].id.replace('{level}', container.level)
        }
}

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

function httpGetAsync(theUrl, callback, level, callbackpath) {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.onreadystatechange = function () {
                if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
                        callback(xmlHttp, level, theUrl, callbackpath);
        }
        xmlHttp.open("GET", theUrl, true); // true for asynchronous 
        xmlHttp.send(null);
}

function ReceiveCall(xmlHttp, level, theUrl, callbackpath) {
        let container_row = document.getElementById('container_row')
        let site_column = document.getElementById('site_column')

        respUrl = xmlHttp.responseURL;
        responseText = xmlHttp.responseText;

        // Restore header if it has been hidden because of an anchor link
        document.getElementById('header').style.display = 'block';

        // Set body width to level * 40 rem
        document.body.style.width = (level * 40 + 200) + 'rem';
        container_row.style.width = (level * 40 + 200) + 'rem';
        site_column.style.width = (level * 40 + 200) + 'rem';

        // Get html
        let text = responseText.split('<div class="container">')[1];
        text = text.split('<!-- end content -->')[0];

        // Close all containers with level below given
        CloseUpperContainers(level);

        // Test if container for this level already exists
        // otherwise create
        let levelcont = document.getElementById('level-' + level);
        let isNew = false
        if (levelcont == null) {
                isNew = true;
                wrappercont = document.createElement('div');
                wrappercont.className = 'container-wrapper';
                wrappercont.id = 'wrapperlevel-' + level;

                container_row.appendChild(wrappercont);

                levelcont = document.createElement('div');
                levelcont.className = 'container';
                levelcont.id = 'level-' + level;
                levelcont.level = level;
        }

        // Update content of div
        levelcont.innerHTML = text;

        if (isNew) {
                document.getElementById('wrapperlevel-' + level).appendChild(levelcont);
        }

        // Get the leventcont again from the DOM
        levelcont = document.getElementById('level-' + level);

        // Scroll into view
        levelcont = document.getElementById('level-' + level);
        //levelcont.scrollIntoView(true);
        //window.scrollTo(window.visualViewport.pageLeft + rem(4), 0);
        SetNoteRight(level);

        // Scroll container to #header link
        theUrl = decodeURI(theUrl);
        if (theUrl.split('#').length > 1) {
                var header_id = theUrl.split('#')[1]
                var el = levelcont.querySelectorAll("#" + header_id)[0];
                if (el) {
                        el.parentElement.scrollTop = el.offsetTop - rem(1);
                }
        } else {
                levelcont.scrollTop = 0;
        }

        // Set url property
        levelcont.url = theUrl.split('#')[0];

        // Arm new links
        SetLinks(level);
        SetContainer(levelcont);

        // Continue path opening (if started with path opening)
        if (callbackpath) {
                OpenPath(level + 1);
        }
        else {
                // Start to build new href like https://localhost:8000/?path=
                let new_href = window.location.pathname + '?path=';

                // Remove https://localhost:8000/ from link name
                let new_tab = theUrl.replace(window.location.origin + '/', '');

                // Add in existing path until the tab where was clicked
                let tab_links = window.location.href.split('?path=');
                if (tab_links.length > 1) {
                        path_to_open = tab_links[1].split('/');
                        for (let i = 0; i < (level - 1); i++) {
                                new_href += path_to_open[i] + '/'
                        }
                }

                // Add in new tab
                new_href += encodeURIComponent(encodeURI(new_tab)) + '/';

                // Set
                window.history.replaceState({}, "", new_href);
        }
}

function CloseUpperContainers(level) {
        // Close all containers that are higher in level than the level
        // of the container in which a link was clicked
        let cns = document.getElementsByClassName("container-wrapper");
        for (let i = 0; i < cns.length; i++) {
                if (cns[i].id) {
                        if (cns[i].id.split('-')[1] > level) {
                                cns[i].remove();
                                CloseUpperContainers(level);
                                return;
                        }
                }
        }
}

function toggle(id, display_value){
        el = document.getElementById(id);
        if (el.style.display == 'none'){
                el.style.display = display_value;
        }
        else if (el.style.display == display_value){
                el.style.display = 'none';
        }        
        else {
                el.style.display = display_value;
        }
}