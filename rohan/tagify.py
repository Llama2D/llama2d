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

driver = uc.Chrome(headless=False,use_subprocess=True,version_main=116)

def tagify_webpage(driver,gt_action):

    pos_candidates = gt_action["pos_candidates"]

    assert len(pos_candidates) == 1,"Only one positive candidate is supported"

    attrs = json.loads(gt_action["pos_candidates"][0]['attributes'])

    cls = attrs.get("class",None)
    id = attrs.get("id",None)

    print(f"Looking for element with class {cls} and id {id}")


    # driver.get(url)
    html = clean_html(driver.page_source)
    soup = BeautifulSoup(html, "html.parser")

    num = 0
    gt_tag_id = -1

    # get gt tag by id
    gt_tag = soup.find(id=id)

    for tag in [*soup.find_all(True)]:

        # get class
        tag_cls = tag.get("class",None)
        if tag_cls is not None:
            tag_cls = " ".join(tag_cls)
        tag_id = tag.get("id",None)

        is_gt_tag = tag_cls == cls and tag_id == id

        if check_interactable_bs4(tag) or is_gt_tag:
            if is_gt_tag:
                print("Found gt element")
            sel_tag = bs4_to_sel(tag, driver)
            tag_whitelist = ["input", "textarea", "select"]
            if sel_tag.text.strip() == "" and sel_tag.tag_name not in tag_whitelist:
                continue
            if check_interactable_sel(sel_tag, driver):

                num += 1

                if is_gt_tag:
                    gt_tag_id = num

                new_text = f"{tag.text} [{num}]"

                script = f"""
                const el = arguments[0];

                const specialTags = ["input", "textarea", "select"];

                const tagLower = el.tagName.toLowerCase();

                if(!specialTags.includes(tagLower))
                    el.innerText = {json.dumps(new_text)};
                else if(tagLower === "input")
                    el.placeholder = {json.dumps(new_text)};
                else if(tagLower === "textarea")
                    el.placeholder = {json.dumps(new_text)};
"""

                driver.execute_script(script, sel_tag)
    return gt_tag_id



if __name__ == "__main__":


    dummy_action = {
        "pos_candidates":[{
            "attributes":{
                "class":"gLFyf",
                "id":"APjFqb"
            }
        }]
    }

    dummy_action = {"pos_candidates":[{'attributes': '{"backend_node_id": "136", "bounding_box_rect": "110,607.390625,264,78", "class": "MuiSelect-root MuiSelect-select jss31 MuiSelect-filled jss32 MuiInputBase-input MuiFilledInput-input jss22 MuiInputBase-inputAdornedStart MuiFilledInput-inputAdornedStart", "id": "reservations-city-search-type", "name": "type", "data_pw_testid_buckeye_candidate": "1"}', 'backend_node_id': '136', 'is_original_target': True, 'is_top_level_target': True, 'tag': 'select'}]}


    driver.get("file:///Users/dooli/Projects/misc/llama2d/961c3a5e-f8ce-4c71-a917-aa546dcea7fb_before.mhtml")
    print(tagify_webpage(driver,dummy_action))