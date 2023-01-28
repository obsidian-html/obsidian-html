'''
#test
#test/sub
#test-multiple
#test_multiple
#testMultiple

#*invalid
# invalid
#invalid!word

#1990
#y1990
#1990y
#19y90

'''

import sys
import os
from pathlib import Path

# add /obsidian-html/ci to path
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent.parent))

# import pb and tests
from unit_tests.unit_test_init import pb, check_test_result, test, \
                                 get_inline_tags


def run_tests():
    cases = [
        {   'name'    : 'Test inline tags recognized - "#test"',
            'function':  get_inline_tags,
            'set'     : (['#test'], ['test'])
        },
        {   'name'    : 'Test inline tags recognized - "#test "',
            'function':  get_inline_tags,
            'set'     : (['#test '], ['test'])
        },
        {   'name'    : 'Test inline tags recognized - "#test/sub"',
            'function':  get_inline_tags,
            'set'     : (['#test/sub'], ['test/sub'])
        },
        {   'name'    : 'Test inline tags recognized - "#test.break"',
            'function':  get_inline_tags,
            'set'     : (['#test.break'], ['test'])
        },
        {   'name'    : 'Test inline tags recognized - "#!invalid"',
            'function':  get_inline_tags,
            'set'     : (['#!invalid'], [])
        },
        {   'name'    : 'Test inline tags recognized - "#1990"',
            'function':  get_inline_tags,
            'set'     : (['#1990'], [])
        },
        {   'name'    : 'Test inline tags recognized - "#y1990"',
            'function':  get_inline_tags,
            'set'     : (['#!invalid'], [])
        },
        {   'name'    : 'Test inline tags recognized - "#1990y"',
            'function':  get_inline_tags,
            'set'     : (['#1990y'], ['1990y'])
        },
        {   'name'    : 'Test inline tags recognized - "#19_90"',
            'function':  get_inline_tags,
            'set'     : (['#19_90'], ['19_90'])
        },
    ]

    # for case in cases:
    #     inp, outp = case['set']
    #     left = '"' + ', '.join(inp) + '"'
    #     print(f"{left : <13}", '-->  ', outp)

    for case in cases:
        test(case)


if __name__ == "__main__":
    os.environ["TESTS_FAILED"] = "0"

    run_tests()

    if (os.environ["TESTS_FAILED"] == '1'):
        sys.exit(1)