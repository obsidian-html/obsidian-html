// GLOBALS
// -----------------------------------------------------------------------------------------------

var SEARCH_DATA = '';                   // search.json contents
var fuse;                               // fuzzy search object
var index;


// Get data
// -----------------------------------------------------------------------------------------------

fetch('{html_url_prefix}/obs.html/data/search.json').then(res => res.json()).then(data => {
    SEARCH_DATA = data;

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
})


// Functions
// -----------------------------------------------------------------------------------------------

function run_search(search_string_id, hard_search_id){
    let search_string_div = document.getElementById(search_string_id);
    let hard_search_div  = document.getElementById(hard_search_id);

    return search(search_string_div.value, hard_search_div.checked);
}

function search(string_search, hard_search){
    // get matches using flexsearch
    results = GetResultsFlex(string_search, hard_search)

    // convert matches to a <ul><li> list
    html = GetHtmlFlex(results, hard_search)

    // make result div grow based on the number of results, with a max height
    let resultsdivbox = document.getElementById('search-results-box')

    let h = results.length * rem(3)
    if (results.length > 0){
        h += rem(2)
    }
    h = Math.min(h, 0.8 * vh())

    resultsdivbox.style.height = h+'px';

    // put results in result div
    let resultsdiv = document.getElementById('search-results')
    resultsdiv.innerHTML = html;
    
    return results
}

function GetResultsFlex(search_string, hard_search){
    let match_ids = []
    let matches = []

    index.search(search_string).forEach(field => {
        field.result.forEach(result => {
            let record_id = result

            // append field to match record
            if (match_ids.includes(record_id)){
                console.log(record_id, 'hit', SEARCH_DATA[record_id].title)
                matches.forEach(match => {
                    if (match.id == record_id){
                        match.matched_on.push(field.field)
                    }
                });
            }
            // add match to list
            else {
                match_ids.push(record_id);
                console.log(record_id, field.field, SEARCH_DATA[record_id].title)
                matches.push({id: record_id, title: SEARCH_DATA[record_id].title, url: SEARCH_DATA[record_id].url, matched_on: [field.field]})                
            }
        })
    });

    return matches
}

function GetResults(string_search, hard_search)
{
    let finds = fuse.search(string_search)
    let results = []

    if (hard_search == false){
            // cut-off based on score. score should be lower (=better) than 0.5
            finds.forEach(find => {
                    if (find.score < 0.5){
                            results.push(find)
                    }
            });
            return results
    }

    // require exact match in title or content keywords
    finds.forEach(find => {
            if (find.item.title.includes(string_search) || find.item.keywords.includes(string_search)){
                    results.push(find)
            }
    });
    return results
}


function GetHtml(fs_results, hard_search){
    html = '<ul>\n'
    fs_results.forEach(res => {
            let summary = ''
            res.matches.forEach(match => {
                    summary += match.value + ' ';
            });
            html += '\t<li><a href="'+res.item.url+'">'+res.item.title+'</a> '
            html += '<span class="score">['+ (100.0 * (1.0 - res.score)).toFixed(2) +']</span> '+ summary +'\n'
    });
    html += '</ul>'
    return html
}

function GetHtmlFlex(fs_results, hard_search){
    html = '<ul>\n'
    fs_results.forEach(res => {
            html += '\t<li onclick="click_inner_link(this)"><a href="'+res.url+'">'+res.title+'</a> '
            //html += '<span class="score">(matched on: '+  res.matched_on.join(", ") +')</span>\n'
            html += '\n'
    });
    html += '</ul>'
    return html
}