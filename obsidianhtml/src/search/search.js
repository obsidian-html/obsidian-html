// GLOBALS
// -----------------------------------------------------------------------------------------------

var SEARCH_DATA = '';                   // search.json contents
var fuse;                               // fuzzy search object
var index;


// Get data
// -----------------------------------------------------------------------------------------------
setTimeout(LoadSearchData, 500);

function LoadSearchData(){
    let search_data = window.localStorage.getItem('search_data');
    let search_hash = window.localStorage.getItem('search_hash');

    if (gzip_hash != search_hash || !search_data){
        // refresh data
        GzipUnzipLocalFile('{html_url_prefix}/obs.html/data/search.json.gzip').then(data => {
            SEARCH_DATA = JSON.parse(data);
            window.localStorage.setItem('search_data', data);
            window.localStorage.setItem('search_hash', gzip_hash);

            InitFlexSearch();
        });
    }
    else {
        // just load cached data
        SEARCH_DATA = JSON.parse(search_data);
        InitFlexSearch();
    }
}

function InitFlexSearch(){
    index = new FlexSearch.Document({
        id: "id",
        index: ["title", "content"],
        tokenize: 'forward'
    });

    let i = 0;
    SEARCH_DATA.forEach(doc => {

        index.add({
            id: i,
            content: doc.keywords,
            title: doc.title,
            url: doc.url
        });

        i++;
    });
}


// Functions
// -----------------------------------------------------------------------------------------------

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
                    .replace('{{content}}', highlight(SEARCH_DATA[res.id].md, search_string, false, 20).join(" "))
    });
    html += '</ul>'
    return html
}

async function GzipUnzipLocalFile(request_url) {
    return fetch(request_url)                                                   // make request
        .then(res => res.blob())                                            // read byte data in blob form and continue when fully read
        .then(blob => blob.arrayBuffer())                                   // convert blob to arraybuffer and continue when done
        .then(ab => {
            data = pako.inflate(ab)                                         // go from zipped arraybuffer to unzipped arraybuffer
            return new TextDecoder('utf-8').decode(new Uint8Array(data));   // convert arraybuffer to string
        })
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