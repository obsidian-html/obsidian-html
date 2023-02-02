import sys
import os
from pathlib import Path

# add /obsidian-html/ci to path
print(str(Path(os.path.realpath(__file__)).parent.parent))
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent))


from unit_tests.tests_md_to_html.codeblocks_in_footnote import run_tests as test_codeblocks_in_footnote
from unit_tests.tests_note_to_md.inline_tags import run_tests as test_inline_tags
from unit_tests.tests_note_to_md.obs_img_to_md import run_tests as test_obs_img_to_md
from unit_tests.tests_post_processing.obs_callout_to_markdown_callout import run_tests as test_obs_callout_to_markdown_callout

os.environ["TESTS_FAILED"] = "0"

test_codeblocks_in_footnote()
test_inline_tags()
test_obs_img_to_md()
test_obs_callout_to_markdown_callout()

if (os.environ["TESTS_FAILED"] == '1'):
    sys.exit(1)