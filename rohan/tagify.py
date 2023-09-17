from .mls_utils import (
    check_interactable_bs4,
    check_interactable_sel,
    clean_html,
    bs4_to_sel,
)
# from reworkd_platform.settings import settings

from bs4 import BeautifulSoup

# create webdriver

import undetected_chromedriver as uc
import json
import os

driver = uc.Chrome(headless=False,use_subprocess=True,version_main=116)

def tagify_webpage(driver,gt_action):

    pos_candidates = gt_action["pos_candidates"]

    assert len(pos_candidates) == 1,"Only one positive candidate is supported"

    attrs = json.loads(gt_action["pos_candidates"][0]['attributes'])

    cls = attrs.get("class",None)
    id = attrs.get("id",None)

    print(f"Looking for element with class {cls} and id {id}")

    # get directory of this file
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    with open(f"{curr_dir}/mlsUtils.js","r") as f:
        driver.execute_script(f.read())

    gt_tag_id = driver.execute_script(f"return tagifyWebpage({json.dumps(cls)},{json.dumps(id)})")
    return gt_tag_id



if __name__ == "__main__":

    print("Starting")

    dummy_action = {
        "pos_candidates":[{
            "attributes":"""{
                "class":"gLFyf",
                "id":"APjFqb"
            }"""
        }]
    }

    # driver.get("https://www.google.com/")

    # input("Press enter to continue")

    dummy_action = {"pos_candidates":[{'attributes': '{"backend_node_id": "136", "bounding_box_rect": "110,607.390625,264,78", "class": "MuiSelect-root MuiSelect-select jss31 MuiSelect-filled jss32 MuiInputBase-input MuiFilledInput-input jss22 MuiInputBase-inputAdornedStart MuiFilledInput-inputAdornedStart", "id": "reservations-city-search-type", "name": "type", "data_pw_testid_buckeye_candidate": "1"}', 'backend_node_id': '136', 'is_original_target': True, 'is_top_level_target': True, 'tag': 'select'}]}


    driver.get("file:///Users/dooli/Projects/misc/llama2d/961c3a5e-f8ce-4c71-a917-aa546dcea7fb_before.mhtml")


    try:
        print(tagify_webpage(driver,dummy_action))


    except Exception as e:
        print(e)

    import time
    time.sleep(5_000)