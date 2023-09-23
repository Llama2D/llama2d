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

url = "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:9999/forums"
# goal = 'close a pop-up if present; navigate to the Contact Us page; if already on the Contact Us page, fill out and submit the "Contact Us" form with generic John Doe info'
goal = "find the username of the user who posted the all-time top post in the Shower Thoughts forum"
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
        y = math.floor(annotation.midpoint_normalized[1] * canvas_height)
        line_cluster[y].append(annotation)

    # Create an empty canvas (list of lists filled with spaces)
    canvas = [[" " for _ in range(canvas_width)] for _ in range(canvas_height)]

    # Place the annotations on the canvas
    for y, line_annotations in line_cluster.items():
        # Sort annotations in this line by x coordinate
        line_annotations.sort(key=lambda x: x.midpoint_normalized[0])

        last_x = 0  # Keep track of the last position where text was inserted
        for annotation in line_annotations:
            x = math.floor(annotation.midpoint_normalized[0] * canvas_width)

            # Move forward if there's an overlap
            x = max(x, last_x)

            # Check if the text fits; if not, move to next line (this is simplistic)
            if x + len(annotation.text) >= canvas_width:
                continue

            # Place the text on the canvas
            for i, char in enumerate(annotation.text):
                canvas[y][x + i] = char

            # Update the last inserted position
            last_x = x + len(annotation.text) + 1  # +1 for a space between words

    # Convert the canvas to a plaintext string
    page_text = "\n".join("".join(row) for row in canvas)
    page_text = "-" * canvas_width + "\n" + page_text + "\n" + "-" * canvas_width
    # print(output)

    return page_text


async def main(page):
    gt_tag_id, id_to_tag = await tagify_webpage(
        page, {"pos_candidates": [{"attributes": "{}"}]}
    )
    await take_screenshot(page, None, screenshot_path)
    page_text = ocr_page_text()

    prompt = f"""Below is an OCR'd web page (using whitespace to approximate its visual structure). I've inserted an ID in brackets (e.g. [24]) before the text of elements that are interactable (e.g. buttons, links).
{page_text}
Your goal is: {goal}
You may perform the following actions: CLICK [id] or TYPE [id] [text].
First, analyze the current state of the page in detail and reason about its contents. Then, decide what action to perform next to make progress toward the goal. State "Action: " followed the chosen action."""
    print(prompt)
    output = await openai_service.completion(
        UserMessage(content=prompt),  # TODO: should use 3.5 here, not 4
    )
    print(output)

    action = output.split("Action: ")[1].strip()
    action_type, action_id, action_text = extract_action_info(action)
    print(action_type, action_id, action_text)

    if action_id is None:
        print("Action ID not found")
        return
    target_el = await page.query_selector(f"xpath={id_to_tag[str(action_id)]}")
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
