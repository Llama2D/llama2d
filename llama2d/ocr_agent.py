import math
from collections import defaultdict
import asyncio
import re
from playwright.async_api import async_playwright
from twocaptcha import TwoCaptcha

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


url = "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:7770/"
goal = "add bushs black beans to the cart"
# goal = 'close a pop-up by any means necessary if present; navigate to the Contact Us page; if already on the Contact Us page, fill out and submit the "Contact Us" form with generic John Doe info'
# goal = "find the username of the user who posted the all-time top post in the Shower Thoughts forum"
screenshot_path = "./screenshot.png"
annotator = ImageAnnotator(
    credentials="/Users/rohan/Documents/llama2d/llama2d/secrets/llama2d-dee298d9a98d.json"
)
openai_service = OpenAIService(settings=settings, model="gpt-4-0613")

solver = TwoCaptcha("3005746e58e3815f4a86727465318d9b")


async def solve_captcha(page) -> str:
    captcha_params = await page.evaluate(
        """(() => {
  if (typeof (___grecaptcha_cfg) !== 'undefined') {
    return Object.entries(___grecaptcha_cfg.clients).map(([cid, client]) => {
      const data = { id: cid, version: cid >= 10000 ? 'V3' : 'V2' };
      const objects = Object.entries(client).filter(([_, value]) => value && typeof value === 'object');

      objects.forEach(([toplevelKey, toplevel]) => {
        const found = Object.entries(toplevel).find(([_, value]) => (
          value && typeof value === 'object' && 'sitekey' in value && 'size' in value
        ));
     
        if (typeof toplevel === 'object' && toplevel instanceof HTMLElement && toplevel['tagName'] === 'DIV'){
            data.pageurl = toplevel.baseURI;
        }
        
        if (found) {
          const [sublevelKey, sublevel] = found;

          data.sitekey = sublevel.sitekey;
          const callbackKey = data.version === 'V2' ? 'callback' : 'promise-callback';
          const callback = sublevel[callbackKey];
          if (!callback) {
            data.callback = null;
            data.function = null;
          } else {
            data.function = callback;
            const keys = [cid, toplevelKey, sublevelKey, callbackKey].map((key) => `['${key}']`).join('');
            data.callback = `___grecaptcha_cfg.clients${keys}`;
          }
        }
      });
      return data;
    });
  }
  return [];
})();
"""
    )
    # print(captcha_params)

    if len(captcha_params) == 1:
        captcha_frame = await page.wait_for_selector("iframe[src*='recaptcha/api2']")
        captcha_frame_content = await captcha_frame.content_frame()

        captcha_checkbox = await captcha_frame_content.wait_for_selector(
            "#recaptcha-anchor"
        )
        await captcha_checkbox.click()

        result = solver.recaptcha(
            sitekey=captcha_params[0]["sitekey"],
            url=captcha_params[0]["pageurl"],
        )
        # print(result)

        captcha_input = await page.query_selector(
            "#g-recaptcha-response"
        )  # TODO: why is this selector not visible?
        await captcha_input.evaluate(
            """(input, captcha_response) => {
            input.value = captcha_response;
        }""",
            result["code"],
        )

        # button = await captcha_frame_content.wait_for_selector("button[type='submit']")
        # await button.click()
        # await page.wait_for_navigation()
        print("captcha solved")
    elif len(captcha_params) > 1:
        print("multiple captchas found")
    else:
        print("no captchas found")


def extract_action_info(s):
    # regex to match action_type, optional action_id, and optional action_text
    pattern = r"(\w+)(?:\s+\[(\d+)\])?(?:\s+\[(.*)\])?"
    match = re.search(pattern, s)

    if match:
        action_type = match.group(1)

        # Check if match.group(2) exists before attempting conversion
        action_id = int(match.group(2)) if match.group(2) else None

        action_text = None
        if action_type == "TYPE":
            action_text = match.group(3)

        return action_type, action_id, action_text

    else:
        return None, None, None


async def execute_action(page, action, id_to_tag):
    action_type, action_id, action_text = extract_action_info(action)
    print(action_type, action_id, action_text)

    if action_type in ("CLICK", "TYPE"):
        if action_id is None:
            print("Action ID not found")
            return
        else:
            el_xpath = id_to_tag[str(action_id)]
            if "iframe" in el_xpath.split("//")[0]:
                # change page context to iframe of iframe_id
                iframe_id = int(el_xpath.split("//")[0].split("_")[1])
                iframes = await page.query_selector_all("iframe")
                page = await iframes[iframe_id].content_frame()
                el_xpath = "//" + el_xpath.split("//")[1]

            target_el = await page.query_selector(f"xpath={el_xpath}")
            if target_el is None:
                print("Target element not found")
                return

    try:
        if "CLICK" in action_type:
            await target_el.scroll_into_view_if_needed()
            await target_el.hover()
            await target_el.click()
        elif "TYPE" in action_type:
            await target_el.scroll_into_view_if_needed()
            await target_el.fill(action_text)
        elif "RETURN" in action_type:  # TODO: update regex for this case (optional id)
            print("ANSWER:", action_text)
        elif "SOLVE_CAPTCHA" in action_type:
            await solve_captcha(page)
    except TimeoutError:
        print("Action timed out")
        return


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


async def agent(page, goal=goal, context=None):
    await asyncio.sleep(2)
    gt_tag_id, id_to_tag = await tagify_webpage(
        page, {"pos_candidates": [{"attributes": "{}"}]}
    )
    await take_screenshot(page, None, screenshot_path)
    page_text = ocr_page_text()

    prompt = f"""Below is an OCR'd web page (using whitespace to approximate its visual structure). I've inserted an ID in brackets (e.g. [24]) before or above the text of elements that are interactable (e.g. buttons, links). For elements you can type text into (e.g. text input or text areas), I've inserted the ID in curly braces.
{page_text}
Your goal is: {goal}
{f"Here is also some information that may be useful: {context}" if context and len(context) else ""}
You may perform the following actions: CLICK [id] (click element), TYPE [id] [text] (type text in element), RETURN [text] (return text to the user e.g. if complete or no good action), SOLVE_CAPTCHA.
First, analyze the current state of the page in detail and reason about its contents. Keep in mind that you may have previously taken some action on this page. Then, decide what action(s) to perform next to make progress toward the goal. State "Actions:" and list the action(s) sequentially (though only 1 may be needed) as a pipe (|) separated list (e.g. "Actions: CLICK [12] | TYPE [29] [hello world]")."""
    # For each action (though only 1 may be needed), state "Action: " on a NEW line followed by your action decision with brackets for its arguments (e.g. "TYPE [35] [hello world]").
    # TODO: maybe use function calling or return as JSON?
    print(prompt)
    output = await openai_service.completion(
        UserMessage(content=prompt),
    )
    print(output)

    actions = output.split("Actions: ")[1]
    if "|" in actions:
        actions = actions.split("|")
    else:
        actions = [actions]
    for action in actions:
        action = action.strip()
        try:
            await execute_action(page, action, id_to_tag)
        except Exception as e:
            print("Unable to execute action:", action, '\nError:', e)

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
            await agent(page)


if __name__ == "__main__":
    asyncio.run(setup_and_run())
