// Keybindings
// ----------------------------------------------------------------------------
OBSHTML_KEYPRESS_FUNCTIONS.push(Tabs_HandleKeyPress)

function Tabs_HandleKeyPress(e) {
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



// Functions 
// ----------------------------------------------------------------------------

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

function ReceiveCall(xmlHttp, level, theUrl, callbackpath) {
    let container_row = document.getElementById('container_row')
    let page_holder = document.getElementById('page_holder')

    respUrl = xmlHttp.responseURL;
    responseText = xmlHttp.responseText;

    // Restore header if it has been hidden because of an anchor link
    document.getElementById('header').style.display = 'block';

    // Set body width to level * 40 rem
    document.body.style.width = (level * 40 + 200) + 'rem';
    container_row.style.width = (level * 40 + 200) + 'rem';
    page_holder.style.width = (level * 40 + 200) + 'rem';

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
            el.parentElement.parentElement.scrollTop = el.offsetTop - rem(1);
        }
    } else {
        levelcont.scrollTop = 0;
    }

    // Set url property
    levelcont.url = theUrl.split('#')[0];

    // Arm new links
    SetContainer(levelcont);
    LoadTableOfContents(levelcont);
    SetLinks(level);

    // Rerender Mathjax
    if (typeof MathJax !== 'undefined'){
        if (typeof MathJax.typeset === 'function'){
            MathJax.typeset();
        }
    }

    // Continue path opening (if started with path opening)
    if (callbackpath) {
        OpenPath(level + 1, callbackpath);
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

// Change link operation
function SetLinks(level) {
    console.log('setting links');
    size_of_rem = getComputedStyle(document.documentElement).fontSize.split("px")[0];
    screen_width_allows_tab_mode = (window.visualViewport.width > (1.2 * 40 * size_of_rem))

    var links = document.getElementsByTagName('a');
    for (let i = 0; i < links.length; i++) {
        let l = links[i];

        // don't overwrite links in these conditions
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
        
        // overwrite links that point to a header on the current page
        if (l.getAttribute("href").includes('#')){
            l.onclick = function () {
                // remove current url from the link
                let current_url = document.URL
                current_url = decodeURI(current_url.replace(window.location.protocol + '//', '').replace(window.location.host, ''))
                current_url = current_url.split('#')[0];

                let link = decodeURI(this.getAttribute("href"))
                link = link.replace(current_url, '')

                // if we are left with something like: '#blabla' then we have an anchor link
                // otherwise, we just open the page
                if (link[0] != '#') {
                    if ((tab_mode && screen_width_allows_tab_mode)){
                        httpGetAsync(this.attributes.href.nodeValue, ReceiveCall, level + 1, false);
                        return false;
                    }
                    else {
                        link = this.getAttribute("href").replace('#', '#!')
                        window.location.href = link;
                        return false;
                    }
                }
                
                // we scroll to the anchor
                // we do this manually because scrolling divs suck
                let levelcont = document.getElementsByClassName("container")[0];
                var el = levelcont.querySelectorAll(link.replaceAll(':', '\\:'))[0];
                if (el) {
                    getParentContainer(el).scrollTop = el.offsetTop - rem(6);
                    el.classList.add('fade-it');
                    setTimeout(function() {
                        el.classList.remove('fade-it');
                     }, 2000);
                }
                return false;
            };
            continue
        }

        // do not overwrite any links that have been set at this point
        if (l.onclick != null) {
            continue;
        }
        // set default link action for tab mode
        if ((tab_mode && screen_width_allows_tab_mode)){
            l.onclick = function () {
                httpGetAsync(this.attributes.href.nodeValue, ReceiveCall, level + 1, false);
                return false;
            };
        }
    }
}


function CenterNote(level) {
    let cont = document.getElementById('level-' + level);
    let margin_left = (window.visualViewport.width - cont.getBoundingClientRect().width) / 2
    let note_left = cont.getBoundingClientRect().left
    window.scrollTo(window.visualViewport.pageLeft - (margin_left - note_left), 0)
}

function SetNoteRight(level) {
    let cont = document.getElementById('level-' + level);
    let w = parseInt(getComputedStyle(cont.parentElement).maxWidth.replace('px', ''));

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


function OpenPath(level, path_to_open) {
    if (path_to_open && path_to_open.length > 0) {
        let path = path_to_open.shift();
        if (path != '') {
            httpGetAsync(path, ReceiveCall, level, path_to_open);
        }
    }
}