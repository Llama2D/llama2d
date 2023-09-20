from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

import io, numpy as np, time
from PIL import Image
import subprocess

options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={user_agent}")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-extensions")
options.add_experimental_option("useAutomationExtension", False)
options.add_experimental_option("excludeSwitches", ["enable-automation"])

options.add_argument("--headless")  # Optional: Run the browser in headless mode
# DEFAULT_CHROMEDRIVER_PATH = 'chromedriver'


def stitch(images):
    stacked_array = np.vstack(images)
    # Convert the NumPy array to a Pillow image
    image = Image.fromarray(stacked_array)

    # Save the image to a file
    image.save("stacked_image.png")


def scrape_scroll(url):
    driver = webdriver.Chrome(options=options)  # Make sure the path to
    # driver = uc.Chrome(headless=True, use_subprocess=False, option)

    driver.get(
        url
    )  # Replace with the URL of the webpage you want to screenshot# Set the initial scroll height
    screenshots = []
    scroll_height = 0
    try:
        while True:
            total_height = driver.execute_script("return document.body.scrollHeight")

            driver.set_window_size(
                1920, total_height
            )  # Adjust the window size to your liking
            screenshot = driver.find_element(By.TAG_NAME, "body").screenshot_as_png

            # print(type(screenshot))
            image = np.array(Image.open(io.BytesIO(screenshot)))
            print(image.shape)
            # with open('screenshot.png', 'wb') as f:
            #     f.write(screenshot)
            screenshots.append(image)
            # Scroll down to the bottom of the page
            # Increment the scroll height
            scroll_height += 1
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # determine if this is end of page
            # Break the loop if we have reached the end of the page
            if scroll_height > 10:  # You can adjust the number of scrolls as needed
                break
    except:
        pass

    finally:
        print(f"Length of screenshots:{len(screenshots)}")
        stitch(screenshots)
        # Close the WebDriver
        driver.quit()


if __name__ == "__main__":
    scrape_scroll("https://www.mytampahomeagent.com/")
