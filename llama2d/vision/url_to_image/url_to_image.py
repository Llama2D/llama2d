from playwright.sync_api import sync_playwright
from PIL import Image
import io

def take_screenshot(url, save_path='screenshot.png', num_screenshots=3):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Set headers
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        })

        print('going to ' + url)
        page.goto(url)

        # Capturing screenshots
        screenshots = []
        for _ in range(num_screenshots):
            # Introduce delay before taking screenshot
            page.wait_for_timeout(2000)  # Wait for 2 seconds
            screenshot = page.screenshot()
            screenshots.append(screenshot)
            page.eval_on_selector("body", "body => { window.scrollBy(0, window.innerHeight); }")

        # Stitch the images together
        images = [Image.open(io.BytesIO(screenshot)) for screenshot in screenshots]
        total_width = images[0].width
        total_height = sum(i.height for i in images)
        stitched_image = Image.new('RGB', (total_width, total_height))

        y_offset = 0
        for img in images:
            stitched_image.paste(img, (0, y_offset))
            y_offset += img.height

        stitched_image.save(save_path)
        
        browser.close()


from urllib.parse import urlparse

def extract_domain(url):
    parsed_uri = urlparse(url)
    domain = '{uri.netloc}'.format(uri=parsed_uri)
    domain = domain.replace('.', '_')
    return domain

# url = input("Enter the URL: ")
# print(extract_domain(url))
if __name__ == "__main__":
    target_url = "https://www.mytampahomeagent.com/"
    path = './extracted/' + extract_domain(target_url) + '.png'
    print(path)

    take_screenshot(
        target_url,
        save_path=path,
        num_screenshots=3
        )
