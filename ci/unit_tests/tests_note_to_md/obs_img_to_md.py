import sys
import os
from pathlib import Path

# add /obsidian-html/ci to path
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent.parent))

# import pb and tests
from unit_tests.unit_test_init import pb, check_test_result, test, \
                                 note2md

def run_tests():
    cases = [
        {   'name'    : 'Test obs image link conversion to md image link - png',
            'function':  note2md.obs_img_to_md_img,
            'set'     : ([pb, '![[test.png]]'], '![](test.png)')
        },
        {   'name'    : 'Test obs image link conversion to md image link - md',
            'function':  note2md.obs_img_to_md_img,
            'set'     : ([pb, '![[test]]'], '<inclusion href="test" />')
        },
        {   'name'    : 'Test obs image link conversion to md image link - png with alias',
            'function':  note2md.obs_img_to_md_img,
            'set'     : ([pb, '![[test.png|alias]]'], '![alias](test.png)')
        },
        {   'name'    : 'Test obs image link conversion to md image link - png with alias that includes size',
            'function':  note2md.obs_img_to_md_img,
            'set'     : ([pb, '![[test.png|alias|100]]'], '![alias|100](test.png)')
        },
    ]

    for case in cases:
        test(case)


if __name__ == "__main__":
    os.environ["TESTS_FAILED"] = "0"

    run_tests()

    if (os.environ["TESTS_FAILED"] == '1'):
        sys.exit(1)