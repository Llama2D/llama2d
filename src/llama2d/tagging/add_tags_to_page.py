import json
import os
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class TagAndBox:
    word: str
    coords: Tuple[int, int]


def add_tags_to_webpage(page, mind2web_action) -> Tuple[int, List[TagAndBox]]:
    """
    Add visual tags to a webpage, and find the tag # of the desired Mind2Web action.
    A visual tag looks like [12] and is superimposed on buttons, textboxes, links, etc.
    """

    attrss = [
        json.loads(pos_candidate["attributes"])
        for pos_candidate in mind2web_action["pos_candidates"]
    ]

    els = []
    for attrs in attrss:
        cls = attrs.get("class", None)
        tag_id = attrs.get("id", None)
        bbox_rect = [float(i) for i in attrs["bounding_box_rect"].split(",")]
        els.append({"cls": cls, "tag_id": tag_id, "bbox_rect": bbox_rect})

    raw_html = mind2web_action["raw_html"]

    # print(f"Looking for element with class {cls}
    # and id {tag_id} and bbox {bbox_rect}")

    curr_dir = os.path.dirname(os.path.realpath(__file__))
    with open(f"{curr_dir}/tagUtils.js", "r") as f:
        page.evaluate(f.read())

    try:
        to_eval = f"tagifyWebpage({json.dumps(els)},true,{json.dumps(raw_html)})"
        gt_tag_id, el_tags = page.evaluate(to_eval)
    except Exception as e:
        raise e
        raise Exception(f"Error evaluating:\n{to_eval}\n{e}")

    assert isinstance(gt_tag_id, int), f"gt_tag_id is {json.dumps(gt_tag_id)}!"

    return gt_tag_id, [TagAndBox(**i) for i in el_tags]


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # get path to current file
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        example_mhtml_path = f"{curr_dir}/../../data/mind2web_example.mhtml"
        example_json_path = f"{curr_dir}/../../data/mind2web_example.json"
        page.goto(f"file://{example_mhtml_path}")
        with open(example_json_path, "r") as f:
            dummy_action = json.load(f)

        try:
            print(add_tags_to_webpage(page, dummy_action))
        except Exception as e:
            print(e)

        input("Press enter to stop the program")
