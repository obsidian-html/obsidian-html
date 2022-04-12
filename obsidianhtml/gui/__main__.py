from obsidianhtml.gui import LaunchInstaller, Launch
from obsidianhtml.gui.Templater import CompileHtml

import sys

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'compile':
            CompileHtml()
        elif sys.argv[1] == 'compile+run':
            CompileHtml()
            #LaunchInstaller()
            Launch()
        else:
            raise Exception(f'Argument {sys.argv[1]} unknown')
    else:
        #LaunchInstaller()
        Launch()

if __name__ == "__main__":
    main()


