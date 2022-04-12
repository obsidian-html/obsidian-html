from ..lib import OpenIncludedFile, GetIncludedFilePath, GetIncludedFilePaths
import regex as re          # regex string finding/replacing

def CompileHtml():
    css = CompileCss(['main', 'flex', 'response','action_components'])
    core_js = CompileJs()
    components = GetComponents()

    for n in GetIncludedFilePaths('installer/units/html'):
        template = OpenIncludedFile(f'installer/units/html/{n}')
        template = template.replace('<css />', css)
        template = template.replace('//{{core}}', core_js)
        template = InsertComponents(components, template)

        n = n.replace('_template.html', '')
        output_path = GetIncludedFilePath(f'installer/{n}.html')
        with open(output_path, 'w', encoding="utf-8") as f:
            f.write(template)

def AddTabs(code, level):
    output = ''
    for l in code.split('\n'):
        output += ('\t'*level) + l + '\n'
    return output

def CompileCss(css_list):
    output = '<style>\n{{css}}\n\t</style>'

    css = []

    for n in css_list:
        css.append(OpenIncludedFile(f'installer/units/style/{n}.css'))

    return output.replace('{{css}}', AddTabs('\n'.join(css), 2))

def CompileJs():
    return AddTabs(OpenIncludedFile(f'installer/units/js/core.js'), 2)

def GetComponents():
    components = {}
    for n in GetIncludedFilePaths('installer/units/components'):
        n = n.replace('.html','')
        components[n] = OpenIncludedFile(f'installer/units/components/{n}.html')
    return components

def InsertComponents(components, html):
    # <input id="select-vault-path" />
    component_tags = re.findall(r'(\<component.*?\>)', html)
    for c in component_tags:
        cid = re.findall(r'(?<=id=")([^"]*)', c)[0]
        comp = AddTabs(components[cid], 1)

        ctype = re.findall(r'(?<=type=")([^"]*)', c)
        if len(ctype) > 0:
            ctype = ctype[0]
            if ctype == 'summary':
                comp = comp.replace('{{config_classes}}', 'hide')
                comp = comp.replace('{{summary_classes}}', '')
            elif ctype == 'config':
                comp = comp.replace('{{config_classes}}', '')
                comp = comp.replace('{{summary_classes}}', 'hide')
            else:
                print(f"error: type {ctype} unknown @ {c}")
                
        html = html.replace(c, comp)

    return html

