'''
#test
#test/sub
#test-multiple
#test_multiple
#testMultiple

#*invalid
# invalid
#invalid!word
'''

import sys
import os
from pathlib import Path

# add /obsidian-html/ci to path
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent.parent))

# import pb and tests
from unit_tests.unit_test_init import pb, check_test_result, test, \
                                 get_inline_tags

os.environ["TESTS_FAILED"] = "0"


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
]

for case in cases:
    test(case)
