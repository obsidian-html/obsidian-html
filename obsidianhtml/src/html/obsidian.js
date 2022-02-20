// Init
// ----------------------------------------------------------------------------
// Globals
var path_to_open = [];

function LoadPage() {
        console.log('threshold', (1.2 * 40 * getComputedStyle(document.documentElement).fontSize.split("px")[0]));
        SetLinks(0);

        // Scroll container to #header link
        if (window.location.hash != '') {
                let el = document.getElementById(window.location.hash.substr(2));
                if (el) {
                        el.parentElement.scrollTop = el.offsetTop - rem(1);
                }
        }


        // Init starting container
        FirstContainer = document.getElementsByClassName('container')[0];
        FirstContainer.id = 'level-0';
        FirstContainer.level = '0';
        SetContainer(FirstContainer);

        // Open the path on loading the page
        // This is everything after ?path=
        var href = window.location.href;
        if (href.includes('?path=')) {
                path_to_open = href.split('?path=')[1].split('/');
                for (let i = 0; i < path_to_open.length; i++) {
                        path_to_open[i] = decodeURIComponent(path_to_open[i]);
                }
        }
        OpenPath(1);
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
                        if (l.classList.contains('anchor-link')) {
                                l.onclick = function () {
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

        // Create clickback element
        cb = document.createElement('div');
        cb.className = 'container-clickback';
        cb.id = 'cb' + container.id;
        container.parentElement.appendChild(cb);

        cb.onclick = function () {
                cont = document.getElementById(this.id.slice(2))
                window.scrollTo(Math.max(window.visualViewport.pageLeft - (70 - cont.getBoundingClientRect().left), 0), 0)
        };

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
        respUrl = xmlHttp.responseURL;
        responseText = xmlHttp.responseText;

        // Restore header if it has been hidden because of an anchor link
        document.getElementById('header').style.display = 'block';

        // Set body width to level * 40 rem
        document.body.style.width = (level * 40 + 200) + 'rem';

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
                document.body.appendChild(wrappercont);

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