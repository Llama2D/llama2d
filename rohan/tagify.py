
from bs4 import BeautifulSoup

# create webdriver
from playwright.sync_api import sync_playwright
# import undetected_chromedriver as uc
import json
import os

# driver = uc.Chrome(headless=False,use_subprocess=True,version_main=116)

def tagify_webpage(page,gt_action):

    pos_candidates = gt_action["pos_candidates"]

    assert len(pos_candidates) == 1,"Only one positive candidate is supported"

    attrs = json.loads(gt_action["pos_candidates"][0]['attributes'])

    cls = attrs.get("class",None)
    id = attrs.get("id",None)

    print(f"Looking for element with class {cls} and id {id}")

    # get directory of this file
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    with open(f"{curr_dir}/mlsUtils.js","r") as f:
        page.execute_script(f.read())

    gt_tag_id = page.execute_script(f"return tagifyWebpage({json.dumps(cls)},{json.dumps(id)})")
    return gt_tag_id



if __name__ == "__main__":

    with sync_playwright() as p:
        # Using the Chromium browser but you can also use 'firefox' or 'webkit'
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto("https://google.com")
        dummy_action = {
            "pos_candidates":[{
                "attributes":"""{
                    "class":"gLFyf",
                    "id":"APjFqb"
                }"""
            }]
        }

        page.goto("file:///Users/dooli/Projects/misc/llama2d/961c3a5e-f8ce-4c71-a917-aa546dcea7fb_before.mhtml")
        dummy_action = {"pos_candidates":[{'attributes': '{"backend_node_id": "136", "bounding_box_rect": "110,607.390625,264,78", "class": "MuiSelect-root MuiSelect-select jss31 MuiSelect-filled jss32 MuiInputBase-input MuiFilledInput-input jss22 MuiInputBase-inputAdornedStart MuiFilledInput-inputAdornedStart", "id": "reservations-city-search-type", "name": "type", "data_pw_testid_buckeye_candidate": "1"}', 'backend_node_id': '136', 'is_original_target': True, 'is_top_level_target': True, 'tag': 'select'}]}

        try:
            print(tagify_webpage(page,dummy_action))
        except Exception as e:
            print(e)

        input("Press enter to stop program")