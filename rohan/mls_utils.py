import asyncio
import re
from typing import List, Optional

# noinspection PyProtectedMember
from bs4 import BeautifulSoup, Tag, Comment
import selenium
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import AnyDriver

# read from env
import os


def clean_html(html: str) -> str:
    raise NotImplementedError("You shouldn't be using any bs4 els")
    soup = BeautifulSoup(html, "html.parser")

    for hidden in soup.select('[style*="display: none"], [hidden], [disabled]'):
        hidden.decompose()

    if soup.head:
        soup.head.decompose()

    for script in soup(["script", "style"]):
        script.decompose()

    for element in soup(text=lambda text: isinstance(text, Comment)):
        element.extract()

    return str(soup.prettify())

def get_xpath(element: Tag) -> str:
    raise NotImplementedError("You shouldn't be using any bs4 els")
    path_parts: List[str] = []
    while element:
        if element.name is None:
            element = element.parent
            continue
        prefix = element.name
        sibling_index = 1  # Start with 1 for XPath indexing
        for sibling in element.previous_siblings:
            if sibling.name == element.name:  # Count only siblings of same type
                sibling_index += 1

        # Add index qualifier if there's more than one sibling of the same type
        if sibling_index > 1 or next(
            filter(lambda sib: sib.name == element.name, element.next_siblings), None  # type: ignore
        ):
            prefix += f"[{sibling_index}]"

        if element.parent is None:
            break
        if element.get("id"):
            prefix += '[@id="' + element["id"] + '"]'
            path_parts.insert(0, prefix)
            return "//" + "/".join(path_parts)  # id is unique, so we can stop here
        elif element.get("class"):
            class_conditions = []
            for single_class in element.get("class"):
                # agnostic to whitespace in class names
                class_conditions.append(
                    f'contains(concat(" ", normalize-space(@class), " "), " {single_class} ")'
                )
            class_conditions_str = " and ".join(class_conditions)
            prefix += f"[{class_conditions_str}]"

        path_parts.insert(0, prefix)
        element = element.parent
    return "//" + "/".join(path_parts)

def bs4_to_sel(element: Tag, driver: AnyDriver) -> WebElement:
    raise NotImplementedError("You shouldn't be using any bs4 els")
    element_path = get_xpath(element)
    by = By.XPATH

    try:
        # TODO: make this search agnostic to whitespace in class names e.g. wadesmithrealestate.com
        # TODO: make this search agnostic to styling changes e.g. matsumlin.com (either track changes to DOM, or reduce xpath specificity)
        # TODO: allow searching over shadow root elements e.g. marimarkrealty.com
        sel_element = driver.find_element(by, element_path)
        return sel_element
    except selenium.common.exceptions.NoSuchElementException:
        # try resetting page state and try again
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        driver.execute_script("window.scrollTo(0, 0);")
        # driver.refresh()

        asyncio.sleep(1)
        try:
            sel_element = driver.find_element(by, element_path)
            return sel_element
        except selenium.common.exceptions.NoSuchElementException:
            pass
        print(f"Could not find element with path {element_path}")

async def write_text(sel_element: WebElement, text: str, driver: AnyDriver) -> None:
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", sel_element
    )
    await asyncio.sleep(1)
    ActionChains(driver).move_to_element(sel_element).click().send_keys_to_element(
        sel_element, text
    ).perform()


def check_interactable_bs4(tag: Tag) -> bool:
    return (
        (tag.name.lower() in ("a", "button", "textarea", "select", "details", "label"))
        or (tag.name.lower() == "input" and tag.get("type") != "hidden")
        or (tag.get("role") == "button")
    )


def check_interactable_sel(sel_element: WebElement, driver) -> bool:
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", sel_element
        )
        _ = sel_element.location
        ActionChains(driver).move_to_element(sel_element).perform()
        return True
    except:
        return False