from obsidianhtml.gui import LaunchInstaller, Launch
from obsidianhtml.gui.Templater import CompileHtml
from obsidianhtml.lib import GetIncludedResourcePath

import sys

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'compile':
            CompileHtml()
        elif sys.argv[1] == 'compile+run':
            CompileHtml()
            Launch()
        else:
            raise Exception(f'Argument {sys.argv[1]} unknown')
    else:
        if isDistFolderPresent() == False:
            CompileHtml()
        Launch()

def isDistFolderPresent():
    return GetIncludedResourcePath('installer/dist').exists()

if __name__ == "__main__":
    main()


