// GLOBALS
// -----------------------------------------------------------------------------------------------

var SEARCH_DATA = '';                   // search.json contents
var fuse;                               // fuzzy search object


// Get data
// -----------------------------------------------------------------------------------------------

fetch('{html_url_prefix}/obs.html/data/search.json').then(res => res.json()).then(data => {
    SEARCH_DATA = data;

    const options = {
            // isCaseSensitive: false,
            includeScore: true,
            // shouldSort: true,
            includeMatches: true,
            // findAllMatches: false,
            // minMatchCharLength: 1,
            // location: 0,
            threshold: 0.5,
            // distance: 100,
            // useExtendedSearch: false,
            ignoreLocation: true,
            // ignoreFieldNorm: false,
            // fieldNormWeight: 1,
            keys: [
            "title",
            "keywords"
            ]
    };                                

    fuse = new Fuse(SEARCH_DATA, options)
    console.log('fuse search loaded');
})


// Functions
// -----------------------------------------------------------------------------------------------

function bsearch(search_string_id, hard_search_id){
    let search_string_div = document.getElementById(search_string_id);
    let hard_search_div  = document.getElementById(hard_search_id);
    console.log(search_string_div.value, hard_search_div.checked);

    return dothing(search_string_div.value, hard_search_div.checked);
}                        

function dothing(string_search, hard_search){
    results = GetResults(string_search, hard_search)
    html = GetHtml(results, hard_search)

    let div = document.getElementById('search')
    div.style.display = 'block';
    let resultsdivbox = document.getElementById('search-results-box')
    resultsdivbox.style.display = 'block';
    let resultsdiv = document.getElementById('search-results')
    resultsdiv.innerHTML = html;
    
    return results
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