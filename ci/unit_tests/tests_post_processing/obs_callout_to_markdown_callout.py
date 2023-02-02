import sys
import os
from pathlib import Path

''' Test conversion from https://help.obsidian.md/How+to/Use+callouts to https://oprypin.github.io/markdown-callouts/#block-level-syntax 
    Requested in https://github.com/obsidian-html/obsidian-html/issues/571
'''

# add /obsidian-html/ci to path
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent.parent))

# import pb and tests
from unit_tests.unit_test_init import pb, paths, get_input_as_str, check_test_result, print_succes, print_fail, \
                                      obs_callout_to_markdown_callout

def run_tests():
    ifn = 'obs_callout_to_markdown_callout'
    cases = [
        {   'name'   : 'Post-processing :: obsidian callout to markdown-callout - Simple note callout',
            'input'  : get_input_as_str(paths, ifn, '1.in.md'),
            'output' : get_input_as_str(paths, ifn, '1.out.md'),
            'arg_dict' : {}
        }, 
        {   'name'   : 'Post-processing :: obsidian callout to markdown-callout - Multi line note callout',
            'input'  : get_input_as_str(paths, ifn, '2.in.md'),
            'output' : get_input_as_str(paths, ifn, '2.out.md'),
            'arg_dict' : {}
        },
        {   'name'   : 'Post-processing :: obsidian callout to markdown-callout - Multi paragraph note callout',
            'input'  : get_input_as_str(paths, ifn, '3.in.md'),
            'output' : get_input_as_str(paths, ifn, '3.out.md'),
            'arg_dict' : {}
        },
        {   'name'   : 'Post-processing :: obsidian callout to markdown-callout - Folding',
            'input'  : get_input_as_str(paths, ifn, '4.in.md'),
            'output' : get_input_as_str(paths, ifn, '4.out.md'),
            'arg_dict' : {}
        },
        {   'name'   : 'Post-processing :: obsidian callout to markdown-callout - Titles',
            'input'  : get_input_as_str(paths, ifn, '5.in.md'),
            'output' : get_input_as_str(paths, ifn, '5.out.md'),
            'arg_dict' : {}
        },
        {   'name'   : 'Post-processing :: obsidian callout to markdown-callout - Titles',
            'input'  : get_input_as_str(paths, ifn, '6.in.md'),
            'output' : get_input_as_str(paths, ifn, '6.out.md'),
            'arg_dict' : {'strict_line_breaks': True}

        },
    ]
    for case in cases:
        check_test_result(case, obs_callout_to_markdown_callout(case['input'], **case['arg_dict']))


if __name__ == "__main__":
    os.environ["TESTS_FAILED"] = "0"

    run_tests()

    if (os.environ["TESTS_FAILED"] == '1'):
        sys.exit(1)
