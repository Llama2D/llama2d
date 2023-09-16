from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

def take_screenshot(url, save_path='image_of_website.png'):
    with sync_playwright() as p:
        # Using the Chromium browser but you can also use 'firefox' or 'webkit'
        browser = p.chromium.launch()
        page = browser.new_page()

        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        })

        print('going to ' + url)
        page.goto(url)
        
        # Set the viewport height to be the height of the content
        content_height = page.evaluate("document.documentElement.scrollHeight")
        page.set_viewport_size({"width": 1920, "height": content_height})  # 1920 width is arbitrary, change if needed
        
        page.screenshot(path=save_path)
        
        browser.close()

def extract_domain(url):
    parsed_uri = urlparse(url)
    domain = '{uri.netloc}'.format(uri=parsed_uri)
    domain = domain.replace('.', '_')
    return domain


if __name__ == "__main__":
    target_url = "https://www.mytampahomeagent.com/"
    # target_url = "https://www.reddit.com"
    path = './extracted/' + extract_domain(target_url) + '.png'
    print(path)

    take_screenshot(
        url=target_url,
        save_path=path
    )
