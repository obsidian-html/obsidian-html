import sys
import os
from pathlib import Path

# https://github.com/obsidian-html/obsidian-html/issues/553

# add /obsidian-html/ci to path
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent.parent))

# import pb and tests
from unit_tests.unit_test_init import pb, paths, get_input_as_str, check_test_result, print_succes, print_fail, \
                                      md2html, convert_codeblocks

def run_tests():
    case = {
        'name'   : 'Replace backtick codeblock with indented block',
        'input'  : 'Test\n```python\nraise Exception("test")\n# bla\n```\nTest',
        'output' : 'Test\n\n    raise Exception("test")\n    # bla\nTest'
    }
    check_test_result(case, convert_codeblocks(case['input']))


    # this just needs to run without erroring out
    # https://github.com/obsidian-html/obsidian-html/issues/553
    case = {
        'name'   : 'Codeblock present in footnote results in a <code> tag',
        'input'  : get_input_as_str(paths, 'codeblocks_in_footnote'),
        'output' : ''
    }
    res = md2html.pythonmarkdown_convert_md_to_html(pb, case['input'], rel_dst_path='')
    if '<code>' in res:
        print_succes(case)
    else:
        print_fail(case)
        print(f"    - Expected '<code>' in output, got:\n{res}")

if __name__ == "__main__":
    os.environ["TESTS_FAILED"] = "0"

    run_tests()

    if (os.environ["TESTS_FAILED"] == '1'):
        sys.exit(1)
