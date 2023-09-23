import json
import os


def add_tags_to_webpage(page, mind2web_action) -> int:
    """
    Add visual tags to a webpage, and find the tag # of the desired Mind2Web action.
    A visual tag looks like [12] and is put next to buttons, textboxes, links, etc.
    """

    pos_candidates = mind2web_action["pos_candidates"]

    assert len(pos_candidates) == 1, "Only one positive candidate is supported"

    attrs = json.loads(mind2web_action["pos_candidates"][0]["attributes"])

    cls = attrs.get("class", None)
    tag_id = attrs.get("id", None)

    print(f"Looking for element with class {cls} and id {tag_id}")

    curr_dir = os.path.dirname(os.path.realpath(__file__))
    with open(f"{curr_dir}/tagUtils.js", "r") as f:
        page.evaluate(f.read())
    # breakpoint()

    gt_tag_id = page.evaluate(f"tagifyWebpage({json.dumps(cls)},{json.dumps(tag_id)})")
    return int(gt_tag_id)


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
