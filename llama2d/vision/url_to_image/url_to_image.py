from urllib.parse import urlparse

from playwright.async_api import async_playwright
from ...constants import SCREEN_RESOLUTION

width, height = SCREEN_RESOLUTION

# def launch_browser


async def take_screenshot(page, url, save_path="image_of_website.png"):
    if page is None:
        async with async_playwright() as p:
            # Using the Chromium browser but you can also use 'firefox' or 'webkit'
            browser = await p.chromium.launch()
            page = await browser.new_page()

            page.set_extra_http_headers(
                {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
                }
            )

            return take_screenshot(page, url, save_path)

    if url is not None:
        print("going to " + url)
        await page.goto(url)

    # Set the viewport height to be the height of the content
    content_height = await page.evaluate("document.documentElement.scrollHeight")
    thresholded_height = min(content_height, height)
    default_viewport_size = page.viewport_size

    await page.set_viewport_size({"width": width, "height": thresholded_height})
    await page.screenshot(path=save_path)

    await page.set_viewport_size(default_viewport_size)


def extract_domain(url):
    parsed_uri = urlparse(url)
    domain = "{uri.netloc}".format(uri=parsed_uri)
    domain = domain.replace(".", "_")
    return domain


if __name__ == "__main__":
    target_url = "https://www.mytampahomeagent.com/"
    # target_url = "https://www.reddit.com"
    path = "./extracted/" + extract_domain(target_url) + ".png"
    print(path)

    take_screenshot(url=target_url, save_path=path)
