import math
from collections import defaultdict
import asyncio
from playwright.async_api import async_playwright
import re

from reworkd_platform.services.openai import OpenAIService, UserMessage
from reworkd_platform.settings import settings

from llama2d.vision.url_to_image import take_screenshot
from llama2d.tagging.tagify import tagify_webpage
from llama2d.vision.ocr import ImageAnnotator

# CBD URLS with Popup:
# https://www.topshelfvapors.net/
# https://www.smokemaestros.com/
# https://boisevg.com/
# http://www.mixnmojosmokeshop.com/
# https://smokecentraltx.com/
# https://headstockshop.myshopify.com/
# https://cloud69smoke.com/


url = "https://smokecentraltx.com/"
goal = 'close a pop-up by any means necessary if present; navigate to the Contact Us page; if already on the Contact Us page, fill out and submit the "Contact Us" form with generic John Doe info'
# goal = "find the username of the user who posted the all-time top post in the Shower Thoughts forum"
screenshot_path = "./screenshot.png"
annotator = ImageAnnotator(
    credentials="/Users/rohan/Documents/llama2d/llama2d/secrets/llama2d-dee298d9a98d.json"
)
openai_service = OpenAIService(settings=settings, model="gpt-4-0613")


def extract_action_info(s):
    # regex to match action_type, action_id and optional action_text
    pattern = r"(\w+)\s+\[(\d+)\](?:\s+\[(.*)\])?"
    match = re.search(pattern, s)

    if match:
        action_type = match.group(1)
        action_id = int(match.group(2))
        action_text = None

        if action_type == "TYPE":
            action_text = match.group(3)

        return action_type, action_id, action_text
    else:
        return None, None, None

async def execute_action(page, action, id_to_tag):
    action_type, action_id, action_text = extract_action_info(action)
    print(action_type, action_id, action_text)

    if action_id is None:
        print("Action ID not found")
        return
    el_xpath = id_to_tag[str(action_id)]
    if 'iframe' in el_xpath.split('//')[0]:
        # change page context to iframe of iframe_id
        iframe_id = int(el_xpath.split('//')[0].split('_')[1])
        iframes = await page.query_selector_all('iframe')
        page = await iframes[iframe_id].content_frame()
        el_xpath = '//' + el_xpath.split('//')[1]
    target_el = await page.query_selector(f"xpath={el_xpath}")
    if target_el is None:
        print("Target element not found")
        return

    if action_type == "CLICK":
        await target_el.scroll_into_view_if_needed()
        await target_el.hover()
        await target_el.click()
    elif action_type == "TYPE":
        await target_el.scroll_into_view_if_needed()
        await target_el.fill(action_text)
    elif action_type == "RETURN":  # TODO: update regex for this case (optional id)
        print("ANSWER:", action_text)


def ocr_page_text():
    annotations = annotator(screenshot_path)

    # Initialize dimensions
    canvas_width = 200
    canvas_height = 100

    # Sort the annotations by their y and then x midpoint_normalized
    annotations = sorted(
        annotations.words,
        key=lambda x: (x.midpoint_normalized[1], x.midpoint_normalized[0]),
    )

    # Cluster tokens by line
    line_cluster = defaultdict(list)
    for annotation in annotations:
        # y = math.floor(annotation.midpoint_normalized[1] * canvas_height)
        y = round(annotation.midpoint_normalized[1], 3)
        line_cluster[y].append(annotation)
    canvas_height = max(canvas_height, len(line_cluster))

    # find max line length
    max_line_length = max(
        sum([len(token.text) + 1 for token in line]) for line in line_cluster.values()
    )
    canvas_width = max(canvas_width, max_line_length)

    # Create an empty canvas (list of lists filled with spaces)
    canvas = [[" " for _ in range(canvas_width)] for _ in range(canvas_height)]

    # Place the annotations on the canvas
    for i, (y, line_annotations) in enumerate(line_cluster.items()):
        # Sort annotations in this line by x coordinate
        line_annotations.sort(key=lambda x: x.midpoint_normalized[0])

        last_x = 0  # Keep track of the last position where text was inserted
        for annotation in line_annotations:
            x = math.floor(annotation.midpoint_normalized[0] * canvas_width)

            # Move forward if there's an overlap
            x = max(x, last_x)

            # Check if the text fits; if not, move to next line (this is simplistic)
            if x + len(annotation.text) >= canvas_width:
                continue  # TODO: extend the canvas_width in this case

            # Place the text on the canvas
            for j, char in enumerate(annotation.text):
                canvas[i][x + j] = char

            # Update the last inserted position
            last_x = x + len(annotation.text) + 1  # +1 for a space between words

    # Convert the canvas to a plaintext string
    page_text = "\n".join("".join(row) for row in canvas)
    page_text = page_text.strip()
    page_text = "-" * canvas_width + "\n" + page_text + "\n" + "-" * canvas_width
    # print(output)

    return page_text


async def main(page):
    await asyncio.sleep(2)
    gt_tag_id, id_to_tag = await tagify_webpage(
        page, {"pos_candidates": [{"attributes": "{}"}]}
    )
    await take_screenshot(page, None, screenshot_path)
    page_text = ocr_page_text()

    prompt = f"""Below is an OCR'd web page (using whitespace to approximate its visual structure). I've inserted an ID in brackets (e.g. [24]) before or above the text of elements that are interactable (e.g. buttons, links). For elements you can type text into (e.g. text input or text areas), I've inserted the ID in curly braces.
{page_text}
Your goal is: {goal}
You may perform the following actions: CLICK [id] (click element), TYPE [id] [text] (type text in element), RETURN [text] (return some info or answer to the user), or NONE (no correct action can be performed).
First, analyze the current state of the page in detail and reason about its contents. Keep in mind that you may have previously taken some action on this page. Then, decide what action(s) to perform next to make progress toward the goal. For each action (though only 1 may be needed), state "Action: " on a new line followed by your action decision with brackets for its arguments (e.g. "TYPE [35] [hello world]")."""
    print(prompt)
    output = await openai_service.completion(
        UserMessage(content=prompt),
    )
    print(output)

    actions = output.split("Action: ")[1:]
    if len(actions) == 1:
        action = actions[0].strip()
        await execute_action(page, action, id_to_tag)
    else:
        for action in actions:
            action = action.strip()
            await execute_action(page, action, id_to_tag)

    return


async def setup_and_run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        page.set_extra_http_headers(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
            }
        )
        await page.goto(url)

        for _ in range(5):
            await main(page)


if __name__ == "__main__":
    asyncio.run(setup_and_run())
