from urllib.parse import urlparse

from ...constants import SCREEN_RESOLUTION
width,height = SCREEN_RESOLUTION

def launch_browser

def take_screenshot(page,url, save_path='image_of_website.png'):
    if url is not None:
        print('going to ' + url)
        page.goto(url)
    
    # Set the viewport height to be the height of the content
    content_height = page.evaluate("document.documentElement.scrollHeight")
    thresholded_height = min(content_height,height)

    page.set_viewport_size({"width": width, "height": thresholded_height})
    
    page.screenshot(path=save_path)

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
