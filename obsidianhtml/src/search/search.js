// GLOBALS
// -----------------------------------------------------------------------------------------------

var SEARCH_DATA_SOURCE = '';                   // search.json contents
var SEARCH_DATA_LOADED = false;
var SEARCH_DATA = [];                          // SEARCH_DATA_SOURCE with changes made

var URL_MODE = '{url_mode}';
var RELATIVE_PATHS = {relative_paths};
var CONFIGURED_HTML_URL_PREFIX = '{configured_html_url_prefix}';
var TRY_PRELOAD = {try_preload};

var fuse;                               // fuzzy search object
var index;


// Get data
// -----------------------------------------------------------------------------------------------
if (TRY_PRELOAD){
    setTimeout(PreLoadSearchData, 500);
}

async function PreLoadSearchData(){
    console.log('Try preloading search_data')
    let search_data = ls_get('search_data');
    if (search_data){
        console.log('Using localStorage seach_data as input')
        SEARCH_DATA_SOURCE = JSON.parse(search_data)

        // start flex search, using SEARCH_DATA_SOURCE as input
        InitFlexSearch();

        // signal that the data is loaded and does not need to be reloaded
        SEARCH_DATA_LOADED = true;

        console.log('Preloading search_data succeeded')
        return
    }
    console.log('Preloading search_data skipped, not (yet) cached in localStorage.')
    return
}

async function LoadSearchData(){
    if (SEARCH_DATA_LOADED){
        console.log('Seach already initialized, skipping LoadSearchData()')
        return
    }

    console.log('Search engine loading...')
    const start = performance.now();

    function end_function(){
        // start flex search, using SEARCH_DATA_SOURCE as input
        InitFlexSearch();

        // signal that the data is loaded and does not need to be reloaded
        SEARCH_DATA_LOADED = true;

        // logging
        console.log('Search engine loaded.')
        const end = performance.now();
        console.log(`Execution time search: ${end - start} ms`);
    }

    // try using cached data
    let search_hash = ls_get('search_hash');
    if (gzip_hash == search_hash)
    {
        // use parsed search_data (ready to be used) if present
        let search_data = ls_get('search_data');
        if (search_data){
            console.log('Using localStorage seach_data as input')
            SEARCH_DATA_SOURCE = JSON.parse(search_data)
            return end_function()
        }

        // use zipped b64 data if present
        let search_data_zipped_b64_str = ls_get('search_data_zipped_b64_str');
        if (search_data_zipped_b64_str)
        {
            console.log('Using localStorage search_data_zipped_b64_str as input')
            let search_data = UnzipData(search_data_zipped_b64_str)
            SEARCH_DATA_SOURCE = JSON.parse(search_data)
            return end_function()
        }
    }

    // no cached data available, get data and cache it when possible
    console.log('Loading search data from file...')

    GetGzipContentsAsB64Str(CONFIGURED_HTML_URL_PREFIX + '/obs.html/data/search.json.gzip').then(gzipped_data_str => {

        ls_set('search_hash', gzip_hash);

        console.log('Unzipping search_data_zipped_b64_str to search_data... ')
        let search_data = UnzipData(gzipped_data_str);
        console.log('Unzipping search_data_zipped_b64_str to search_data... Done')

        console.log('Try caching search_data... ')
        try {
            ls_set('search_data', search_data);
            console.log('Caching search_data... Done')
        } 
        catch (error) {
            console.error(error);
            console.log('Caching search_data... Failed')

            console.log('Try Caching search_data_zipped_b64_str... ')
            try {
                ls_set('search_data_zipped_b64_str', gzipped_data_str);
                console.log('Caching search_data_zipped_b64_str... Done.')
            } 
            catch (error) {
                console.error(error);
                console.log('Caching search_data_zipped_b64_str... Failed')
            }
        }

        SEARCH_DATA_SOURCE = JSON.parse(search_data);
        console.log('Loading search data from file... Done')
        
        return end_function()
    })
}

function InitFlexSearch(){
    index = new FlexSearch.Document({
        id: "id",
        index: ["title", "content"],
        tokenize: 'forward'
    });

    let i = 0;
    SEARCH_DATA_SOURCE.forEach(doc => {
        let obj = {
            id: i,
            //content: doc.keywords,
            content: doc.content,
            title: doc.title,
            url: get_node_url_adaptive(doc)
        }
        index.add(obj);

        doc.url = obj.url;
        SEARCH_DATA.push(doc);

        i++;
    });
}


// Functions
// -----------------------------------------------------------------------------------------------
function get_node_url_adaptive(node){
    if (URL_MODE == 'relative'){
        return CONFIGURED_HTML_URL_PREFIX + '/' + node.rtr_url;
    }
    if (URL_MODE == 'absolute'){
        return node.url;
    }
    throw 'OBS.HTML: URL_MODE should be either "absolute" or "relative"! Search failed to get node url.';
}

function run_search(search_string_id, hard_search_id) {
    let search_string_div = document.getElementById(search_string_id);
    let hard_search_div = document.getElementById(hard_search_id);

    return search(search_string_div.value, hard_search_div.checked);
}

function search(string_search, hard_search) {
    // get matches using flexsearch
    results = GetResultsFlex(string_search, hard_search)

    // convert matches to a <ul><li> list
    html = GetHtmlFlex(results, string_search, hard_search)

    // make result div grow based on the number of results, with a max height
    let resultsdivbox = document.getElementById('search-results-box')

    let h = results.length * rem(6)
    if (results.length > 0) {
        h += rem(2)
    }
    h = Math.min(h, 0.8 * vh())

    resultsdivbox.style.height = h + 'px';

    // put results in result div
    let resultsdiv = document.getElementById('search-results')
    resultsdiv.innerHTML = html;

    return results
}

function GetResultsFlex(search_string, hard_search) {
    let match_ids = []
    let matches = []

    index.search(search_string).forEach(field => {
        field.result.forEach(result => {
            let record_id = result

            // append field to match record
            if (match_ids.includes(record_id)) {
                matches.forEach(match => {
                    if (match.id == record_id) {
                        match.matched_on.push(field.field)
                    }
                });
            }
            // add match to list
            else {
                match_ids.push(record_id);
                matches.push({ id: record_id, title: SEARCH_DATA[record_id].title, url: SEARCH_DATA[record_id].url, matched_on: [field.field] })
            }
        })
    });

    return matches
}

function GetHtmlFlex(fs_results, search_string, hard_search) {
    let template = `
<li>
    <div class="search-result-title">
        <div class="search-result-title-name" onclick="click_list_link(this)">
            <a href="{{url}}">{{title}}</a>
        </div>
        <div class="search-result-icon" onclick="toggle(this.parentElement.parentElement);"> 
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ChevronDown"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </div>
    </div>
    <div class="search-highlights" onclick="click_list_link(this)">'
        {{content}}
    </div>
</li>
`;

    html = '<ul>\n'
    fs_results.forEach(res => {
        let element = template;
        html += element.replace('{{url}}', res.url)
                    .replace('{{title}}', res.title)
                    .replace('{{content}}', highlight(SEARCH_DATA[res.id].content, search_string, false, 20).join(" "))
    });
    html += '</ul>'
    return html
}

async function GzipUnzipLocalFile(request_url) {
    return fetch(request_url)                                               // make request
        .then(res => res.blob())                                            // read byte data in blob form and continue when fully read
        .then(blob => blob.arrayBuffer())                                   // convert blob to arraybuffer and continue when done
        .then(ab => {
            data = pako.inflate(ab)                                         // go from zipped arraybuffer to unzipped arraybuffer
            return new TextDecoder('utf-8').decode(new Uint8Array(data));   // convert arraybuffer to string
        })
}

async function GetGzipContentsAsB64Str(request_url) {
    console.log('Refreshing search data')
    return fetch(request_url)                                               // make request
        .then(res => res.blob())                                            // read byte data in blob form and continue when fully read
        .then(blob => blob.arrayBuffer())                                   // convert blob to arraybuffer and continue when done
        .then(ab => {
            return array_buffer_to_b64_str(ab)
        })
}

function array_buffer_to_utf8_str(ab){
    var enc = new TextDecoder("utf-8");
    let str = enc.decode(ab);
    return str;
}

function array_buffer_to_b64_str( buffer ) {
    var binary = '';
    var bytes = new Uint8Array( buffer );
    var len = bytes.byteLength;
    for (var i = 0; i < len; i++) {
        binary += String.fromCharCode( bytes[ i ] );
    }
    return window.btoa( binary );
}

function b64_str_to_array_buffer(base64) {
    var binary_string = window.atob(base64);
    var len = binary_string.length;
    var bytes = new Uint8Array(len);
    for (var i = 0; i < len; i++) {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}

function UnzipData(gzipped_data_str){
    let zipped_ab = b64_str_to_array_buffer(gzipped_data_str);
    data_ab = pako.ungzip(zipped_ab);
    data_str = array_buffer_to_utf8_str(data_ab);
    return data_str;
}


function highlight(input_string, match_string, match_middle, border) {
    let s = input_string;
    let m = match_string;

    let m_len = m.length;
    let match_index = 0;

    let match_start = [];
    let match_end = [];

    let nonwordchars2 = '[]() \n.,`↩#…;'  // don't include /,<,> lest the <em> tags are disturbed in a later step.
    let nonwordchars = nonwordchars2 + '/<>'

    function html_encode(ch){
        if (ch == '<'){
            return '&lt;'
        }
        if (ch == '>'){
            return '&gt;'
        }
        return ch
    }

    // Find match starts and ends
    for (let i = 0; i < s.length; i++) {
        let ch = s[i];

        // reset matching if mismatch
        if (ch != m[match_index]) {
            match_index = 0;
            // remove last match_start if it never completed
            if (match_start.length > match_end.length){
                match_start.pop()
            }
        }
        // advance match index when matching, and keep track of start and end of match
        if (ch == m[match_index]) {
            if (match_index == 0) {
                // if match_middle == false, the character left of the first match should be a space, or the i should be 0
                if (match_middle || i == 0 || nonwordchars.includes(s[i-1])) {
                    match_start.push(i)
                }
                else {
                    continue;
                }
            }
            
            if (match_index == m_len - 1) {
                match_end.push(i)
            }
            match_index += 1;
        }
        // set up new matching if match complete
        if (match_index == m_len) {
            match_index = 0
        }
    }

    // remove last match_start if it never completed
    if (match_start.length > match_end.length){
        match_start.pop()
    }

    // get chunks containing one match each + the border number of characters
    let chunks = []
    for (let i = 0; i < match_start.length; i++) {
        let ms = match_start[i];
        let me = match_end[i];
        let start = Math.max(0, ms - border);
        let end = Math.min(s.length, me + border + 1);

        let chunk = s.substring(start, end);

        // add emphasis
        let emph_chunk = ''

        let hl_start = ms - start
        let hl_end = hl_start + (me - ms);

        for (let i = 0; i < chunk.length; i++) {
            if (i == hl_start){
                emph_chunk += '<em>'
            }
            emph_chunk += html_encode(chunk[i])
            if (i == hl_end){
                emph_chunk += '</em>'
            }
        }
        chunk = emph_chunk;

        // add ellipsis
        if (start != 0){
            chunk = '…'+chunk
        }
        if (end != s.length){
            chunk += '…'
        }

        // make gray every nonwordchar
        gr_chunk = ''
        in_gray = false
        for (let i = 0; i < chunk.length; i++) {
            let ch = chunk[i]
            if (nonwordchars2.includes(ch)){
                if (in_gray){
                    gr_chunk += ch
                    continue
                }
                else {
                    in_gray = true;
                    gr_chunk += '<g>' + ch
                    continue
                }
            }
            else {
                if (in_gray){
                    in_gray = false;
                    gr_chunk += '</g>' + ch
                    continue
                }
                else {
                    gr_chunk += ch
                    continue
                }
            }
        }
        if (in_gray){
            gr_chunk += '</g>'
        }
        chunk = gr_chunk

        chunks.push(chunk)
    }

    return chunks
}