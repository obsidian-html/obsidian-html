import sys
import os
from pathlib import Path

# add /obsidian-html/ci to path
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent.parent))

# import pb and tests
from unit_tests.unit_test_init import pb, check_test_result,\
                                 obs_img_to_md_img

os.environ["TESTS_FAILED"] = "0"


# run img tests

case = {
    'name'   : 'Test obs image link conversion to md image link - png',
    'input'  : '![[test.png]]',
    'output' : '![](test.png)'
}
check_test_result(case, obs_img_to_md_img(pb, case['input']))

case = {
    'name'   : 'Test obs image link conversion to md image link - md',
    'input'  : '![[test]]',
    'output' : '<inclusion href="test" />'
}
check_test_result(case, obs_img_to_md_img(pb, case['input']))

if (os.environ["TESTS_FAILED"] == '1'):
    sys.exit(1)