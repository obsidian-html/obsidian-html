from ..lib import OpenIncludedFile, GetIncludedResourcePath, GetIncludedFilePaths
import regex as re


def CompileHtml():
    # load reusable code to put in the templates
    css = CompileCss(["main", "flex", "response", "action_components", "error"])
    core_js = CompileJs()
    components = GetComponents()

    # ensure dist folder is present (this allows us to delete this folder wholesale)
    GetIncludedResourcePath("installer/dist/").mkdir(parents=True, exist_ok=True)

    # compile files from templates and write to obsidianhtml/src/installer/dist/
    for n in GetIncludedFilePaths("installer/units/html"):
        template = OpenIncludedFile(f"installer/units/html/{n}")
        template = template.replace("<css />", css)
        template = template.replace("//{{core}}", core_js)
        template = InsertComponents(components, template)

        n = n.replace("_template.html", "")
        output_path = GetIncludedResourcePath(f"installer/dist/{n}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(template)

    # put warning readme in the folder
    text = "The files in this folder are compiled from the files in the units folder.\nEditing the folders here has no use."
    with open(GetIncludedResourcePath("installer/dist/readme.md"), "w", encoding="utf-8") as f:
        f.write(text)


def AddTabs(code, level):
    output = ""
    for l in code.split("\n"):
        output += ("\t" * level) + l + "\n"
    return output


def CompileCss(css_list):
    # combine all the css files together into one block and return wrapped in a style tag
    css = []
    for n in css_list:
        css.append(OpenIncludedFile(f"installer/units/style/{n}.css"))

    return "<style>\n" + AddTabs("\n".join(css), 2) + "\n\t</style>"


def CompileJs():
    return AddTabs(OpenIncludedFile("installer/units/js/core.js"), 2)


def GetComponents():
    components = {}
    for n in GetIncludedFilePaths("installer/units/components"):
        n = n.replace(".html", "")
        components[n] = OpenIncludedFile(f"installer/units/components/{n}.html")
    return components


def InsertComponents(components, html):
    # <component id="select-vault-path" type="config" />
    # or
    # <component id="select-vault-path" type="summary" />
    # etc

    # Do a regex replacement of component tags in the html, with the code in the
    # corresponding component files.
    component_tags = re.findall(r"(\<component.*?\>)", html)
    for uid, c in enumerate(component_tags):
        cid = re.findall(r'(?<=id=")([^"]*)', c)[0]
        comp = AddTabs(components[cid], 1)

        # Find the value in `type="<value>"` within the component tag
        # and adjust the output based on the type.
        ctype = re.findall(r'(?<=type=")([^"]*)', c)
        if len(ctype) > 0:
            ctype = ctype[0]
            if ctype == "summary":
                comp = comp.replace("{{config_classes}}", "hide")
                comp = comp.replace("{{summary_classes}}", "")
            elif ctype == "config":
                comp = comp.replace("{{config_classes}}", "")
                comp = comp.replace("{{summary_classes}}", "hide")
            else:
                print(f"error: type {ctype} unknown @ {c}")

        # Replace all occurences of {{uid}} with a unique number (for this page)
        comp = comp.replace("{{uid}}", str(uid))

        # insert into html code
        html = html.replace(c, comp)

    return html
