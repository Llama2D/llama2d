# import webdriver
from selenium import webdriver

# import Action chains
from selenium.webdriver.common.action_chains import ActionChains


def run(driver, action):
    menu = driver.find_element_by_css_selector(".nav")
    hidden_submenu = driver.find_element_by_css_selector(".nav # submenu1")

    ActionChains(driver).move_to_element(menu).click(hidden_submenu).perform()
    # Or actions can be queued up one by one, then performed.:

    menu = driver.find_element_by_css_selector(".nav")
    hidden_submenu = driver.find_element_by_css_selector(".nav # submenu1")

    actions = ActionChains(driver)
    actions.move_to_element(menu)
    actions.click(hidden_submenu)
    actions.perform()


# Project Example –
# create webdriver object
# get geeksforgeeks.org
driver.get("https://www.geeksforgeeks.org/")
# get element
element = driver.find_element_by_link_text("Courses")
# create action chain object
action = ActionChains(driver)

# click the item
action.click(on_element=element)

# perform the operation
action.perform()


if "__main__" == __name__:
    # create webdriver object
    driver = webdriver.Firefox()
    # create action chain object
    action = ActionChains(driver)
    run(driver, action)
