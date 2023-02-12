import sys
import os
from pathlib import Path
from termcolor import colored

# add /obsidian-html/ci to path
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent))

# get relevant paths
from tests.lib import get_paths
paths = get_paths()

# add /obsidian-html to path
sys.path.insert(1, str(paths['root']))

# build picknickbasket
from obsidianhtml.core.PicknickBasket import PicknickBasket
pb = PicknickBasket()

# create input dict so that we can set the entrypoint dynamically
input_cfg = {}
input_cfg['obsidian_entrypoint_path_str'] = paths['test_entrypoint'].resolve().as_posix()
pb.user_config_dict = input_cfg

# finish creation of picknickbasket
pb.construct('')

# set color output
is_windows = hasattr(sys, 'getwindowsversion')
if is_windows:
    os.system('color')

# import functions to test
from obsidianhtml import note2md
from obsidianhtml import md2html
from obsidianhtml.parser.MarkdownPage import get_inline_tags
from obsidianhtml.markdown_extensions.FootnoteExtension import convert_codeblocks
from obsidianhtml.features.post_processing import obs_callout_to_markdown_callout


def check_test_result(case, output):
    def show_whitespace(s):
        return s.replace(' ', '·').replace('\n', '↲\n')
    if output != case['output']:
        print_fail(case)
        print(f"Expected:\n{show_whitespace(case['output'])}")
        print(f"Got:\n{show_whitespace(output)}")
        os.environ["TESTS_FAILED"] = "1"
    else:
        print_succes(case)


def test(case):
    # run function
    if 'set' in case:
        function_input, expected_output = case['set']
        output = case['function'](*function_input)
    else:
        raise Exception('not implemented')

    if output != expected_output:
        print_fail(case)
        print(f"    - Expected:\n{expected_output}")
        print(f"    - Got:\n{output}")
        os.environ["TESTS_FAILED"] = "1"
    else:
        print_succes(case)

def print_succes(case):
    print(colored(f"✓  {case['name']}", 'green'))

def print_fail(case):
    print(colored(f"X  {case['name']}", 'red'))

def get_input_as_str(paths, foldername, input_file_name='input.md'):
    path = paths['unit_test_input_output_folder'].joinpath(foldername).joinpath(input_file_name)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()