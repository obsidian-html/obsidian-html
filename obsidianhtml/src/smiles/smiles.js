var smiles_theme  = "{smiles_theme}";
var smiles_width  = "{smiles_width}";
var smiles_height = "{smiles_height}";

var smilesOptions = {
    scale: 0,
    shortBondLength: 0.8,
    bondLength: 15,
    bondSpacing: 1.8,
    width: 500,   // updated elsewhere before use
    height: 500,  // updated elsewhere before use
    atomVisualization: 'default',
    isomeric: true,
    debug: false,
    terminalCarbons: false,
    explicitHydrogens: true,
    compactDrawing: true,
    fontFamily: 'Arial, Helvetica, sans-serif',
    experimentalSSSR: true,
    kkThreshold: 0.1,
    kkInnerThreshold: 0.1,
    kkMaxIteration: 20000,
    kkMaxInnerIteration: 50,
    kkMaxEnergy: 1000000000,
	fontSizeLarge: 5,
	fontSizeSmall: 3,
	padding: 2,

	bondThickness: 0.5,
	overlapSensitivity: 0.42,
	overlapResolutionIterations: 1,


    themes: {
        dark: {
            C: '#fff',
            O: '#e74c3c',
            N: '#3498db',
            F: '#27ae60',
            CL: '#16a085',
            BR: '#d35400',
            I: '#8e44ad',
            P: '#d35400',
            S: '#f1c40f',
            B: '#e67e22',
            SI: '#e67e22',
            H: '#aaa',
            BACKGROUND: '#141414',
        },
        light: {
            C: '#222',
            O: '#e74c3c',
            N: '#3498db',
            F: '#27ae60',
            CL: '#16a085',
            BR: '#d35400',
            I: '#8e44ad',
            P: '#d35400',
            S: '#f1c40f',
            B: '#e67e22',
            SI: '#e67e22',
            H: '#666',
            BACKGROUND: '#fff',
        },
        oldschool: {
            C: '#000',
            O: '#000',
            N: '#000',
            F: '#000',
            CL: '#000',
            BR: '#000',
            I: '#000',
            P: '#000',
            S: '#000',
            B: '#000',
            SI: '#000',
            H: '#000',
            BACKGROUND: '#fff',
        },
        'oldschool-dark': {
            C: '#fff',
            O: '#fff',
            N: '#fff',
            F: '#fff',
            CL: '#fff',
            BR: '#fff',
            I: '#fff',
            P: '#fff',
            S: '#fff',
            B: '#fff',
            SI: '#fff',
            H: '#fff',
            BACKGROUND: '#000',
        },
        solarized: {
            C: '#586e75',
            O: '#dc322f',
            N: '#268bd2',
            F: '#859900',
            CL: '#16a085',
            BR: '#cb4b16',
            I: '#6c71c4',
            P: '#d33682',
            S: '#b58900',
            B: '#2aa198',
            SI: '#2aa198',
            H: '#657b83',
            BACKGROUND: '#fff',
        },
        'solarized-dark': {
            C: '#93a1a1',
            O: '#dc322f',
            N: '#268bd2',
            F: '#859900',
            CL: '#16a085',
            BR: '#cb4b16',
            I: '#6c71c4',
            P: '#d33682',
            S: '#b58900',
            B: '#2aa198',
            SI: '#2aa198',
            H: '#839496',
            BACKGROUND: '#fff',
        },
        matrix: {
            C: '#678c61',
            O: '#2fc079',
            N: '#4f7e7e',
            F: '#90d762',
            CL: '#82d967',
            BR: '#23755a',
            I: '#409931',
            P: '#c1ff8a',
            S: '#faff00',
            B: '#50b45a',
            SI: '#409931',
            H: '#426644',
            BACKGROUND: '#fff',
        },
        github: {
            C: '#24292f',
            O: '#cf222e',
            N: '#0969da',
            F: '#2da44e',
            CL: '#6fdd8b',
            BR: '#bc4c00',
            I: '#8250df',
            P: '#bf3989',
            S: '#d4a72c',
            B: '#fb8f44',
            SI: '#bc4c00',
            H: '#57606a',
            BACKGROUND: '#fff',
        },
        carbon: {
            C: '#161616',
            O: '#da1e28',
            N: '#0f62fe',
            F: '#198038',
            CL: '#007d79',
            BR: '#fa4d56',
            I: '#8a3ffc',
            P: '#ff832b',
            S: '#f1c21b',
            B: '#8a3800',
            SI: '#e67e22',
            H: '#525252',
            BACKGROUND: '#fff',
        },
        cyberpunk: {
            C: '#ea00d9',
            O: '#ff3131',
            N: '#0abdc6',
            F: '#00ff9f',
            CL: '#00fe00',
            BR: '#fe9f20',
            I: '#ff00ff',
            P: '#fe7f00',
            S: '#fcee0c',
            B: '#ff00ff',
            SI: '#ffffff',
            H: '#913cb1',
            BACKGROUND: '#fff',
        },
        gruvbox: {
            C: '#665c54',
            O: '#cc241d',
            N: '#458588',
            F: '#98971a',
            CL: '#79740e',
            BR: '#d65d0e',
            I: '#b16286',
            P: '#af3a03',
            S: '#d79921',
            B: '#689d6a',
            SI: '#427b58',
            H: '#7c6f64',
            BACKGROUND: '#fbf1c7',
        },
        'gruvbox-dark': {
            C: '#ebdbb2',
            O: '#cc241d',
            N: '#458588',
            F: '#98971a',
            CL: '#b8bb26',
            BR: '#d65d0e',
            I: '#b16286',
            P: '#fe8019',
            S: '#d79921',
            B: '#8ec07c',
            SI: '#83a598',
            H: '#bdae93',
            BACKGROUND: '#282828',
        },
        custom: {
            C: '#222',
            O: '#e74c3c',
            N: '#3498db',
            F: '#27ae60',
            CL: '#16a085',
            BR: '#d35400',
            I: '#8e44ad',
            P: '#d35400',
            S: '#f1c40f',
            B: '#e67e22',
            SI: '#e67e22',
            H: '#666',
            BACKGROUND: '#fff',
        },
    },
};

function load_smiles(){
    function add_svg(parent_div, svg_id, width, height, smallest){
        let wrapper_div = document.createElement('div')
        wrapper_div.classList.add("smiles_canvas")
        wrapper_div.style.width  = width+"px";           // default, gets overwritten by smilesdrawer
        wrapper_div.style.height = height+"px";           // default, gets overwritten by smilesdrawer
        parent_div.appendChild(wrapper_div)

        let div = document.createElement('div')
        div.style.margin = "auto";
        div.style.width  = smallest+"px";           // default, gets overwritten by smilesdrawer
        div.style.height = smallest+"px";           // default, gets overwritten by smilesdrawer
        wrapper_div.appendChild(div)

        div.innerHTML += '<svg id="'+svg_id+'" viewbox="0 0 '+height+' '+width+'" xmlns="http://www.w3.org/2000/svg"></svg>';
        
    }

    blocks = document.getElementsByClassName("lang-smiles");
    let c = 0;
    for (let i=0;i<blocks.length;i++)
    {
        let block = blocks[i];
        let text = block.innerText;
        let formulas = text.split(/\r?\n/);

        // determine width and height of canvas
        let smw = 500;
        if (smiles_width.includes("%")){
            smw = block.clientWidth;
        }
        else {
            smw = parseInt(smiles_width);
        }

        let smh = 500;
        if (smiles_height.includes("%")){
            smh = block.clientHeight;
        }
        else {
            smh = parseInt(smiles_height);
        }

        let smallest = smw;
        if (smh < smallest){
            smallest = smh;
        }
        smilesOptions["width"] = smallest;
        smilesOptions["height"] = smallest;

        let smilesDrawer = new SmilesDrawer.SvgDrawer(smilesOptions);

        // remove all block contents
        block.innerHTML = "";

        // make one canvas per formula in the block
        for (let j=0;j<formulas.length;j++)
        {
            if (j > 10){
                return
            }
            let formula = formulas[j];
            if (formula.trim() == ""){
                continue;
            }
            c = c + 1;
            let svg_id = "smiles-svg-"+c;
            
            // add canvas to draw in
            add_svg(block, svg_id, smw, smh, smallest);

            // draw molecule in canvas
            try {
                SmilesDrawer.parse(formula, function(tree) {
                    smilesDrawer.draw(tree, svg_id, smiles_theme, false);
                });
            }
            catch {}

        }
    };
}
document.addEventListener('DOMContentLoaded', load_smiles);

function reset_smiles(){
    // remove old canvasses
    const elements = document.getElementsByClassName("smiles_canvas");
    while(elements.length > 0){
        elements[0].parentNode.removeChild(elements[0]);
    }

    // reapply smiles
    load_smiles()
}