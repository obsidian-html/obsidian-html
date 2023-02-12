import sys
import os
from pathlib import Path

# https://github.com/obsidian-html/obsidian-html/issues/553

# add /obsidian-html/ci to path
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent.parent))

# import pb and tests
from unit_tests.unit_test_init import pb, paths, get_input_as_str, test, check_test_result, print_succes, print_fail, \
                                      md2html, convert_codeblocks

def run_tests():
    pass


if __name__ == "__main__":
    os.environ["TESTS_FAILED"] = "0"

    run_tests()

    if (os.environ["TESTS_FAILED"] == '1'):
        sys.exit(1)