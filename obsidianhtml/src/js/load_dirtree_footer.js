// load dirtree as left-pane
function load_dirtree_as_left_pane(xmlHttp, level, theUrl, callbackpath) {
    const jsonData = JSON.parse(xmlHttp.responseText);
    let filename = ''
    let folder = ''

    let cpd = document.getElementById(dir_index_pane_div)
    if (!cpd){
        return false
    }

    // get current node
    for (let i = 0; i < jsonData.nodes.length; i++) {
        let node = jsonData.nodes[i];
        if (node.id == CURRENT_NODE) {
            // disable content nav if configured on the node
            if ("obs.html" in node.metadata && "disable_dir_nav" in node.metadata['obs.html']) {
                if (node.metadata['obs.html'].disable_dir_nav) {
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
    if (filename == '') {
        cpd.style.maxWidth = '0.7rem'
        cpd.style.minWidth = '0.7rem'
        cpd.style.padding = '0rem'
        return
    }

    // get all links in the same folder
    let links = []
    for (let i = 0; i < jsonData.nodes.length; i++) {
        let node = jsonData.nodes[i];
        if (node.url.startsWith(folder) == false) {
            continue;
        }

        let url = node.url
        if (folder != '') {
            url = url.replace(folder + '/', '')
        }
        if (url[0] == '/') {
            url = url.substring(1);
        }
        if (url.includes('/')) {
            continue
        }
        if (node.url[0] != '/') {
            node.url = '/' + node.url;
        }
        links.push({ 'id': node.id, 'url': node.url })
    }

    // skip if no links found        
    if (links.length < 2) {
        return
    }

    // sort list alphabetically
    function compare_lname(a, b) {
        if (a.id.toLowerCase() < b.id.toLowerCase()) {
            return -1;
        }
        if (a.id.toLowerCase() > b.id.toLowerCase()) {
            return 1;
        }
        return 0;
    }

    links.sort(compare_lname);

    let html = ''
    header = 'Directory Contents'
    html += '<span class="toc-header">' + header + '</span><ul>'
    for (let i = 0; i < links.length; i++) {
        if (links[i].id == CURRENT_NODE) {
            html += '<li class="current_page_link"><a href="' + links[i].url + '">' + links[i].id + '</a></li>'
        }
        else {
            html += '<li><a href="' + links[i].url + '">' + links[i].id + '</a></li>'
        }
    }
    html += '</ul>'

    cpd.innerHTML = html;
}