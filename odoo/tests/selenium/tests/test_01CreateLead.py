# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


@pytest.mark.usefixtures("get_parameters", "setup_hostpage")
class Test06CreateLead:
    @pytest.mark.dependency(scope="session", name="06", depends=["05"])
    def test_06_create_lead(self, get_parameters, setup_hostpage):
        driver = setup_hostpage
        basetimeout = get_parameters["basetimeout"] * 1000

        # Check if user is logged in
        homemenucount = len(driver.find_elements(By.XPATH, "//nav/a"))
        appiconcount = len(driver.find_elements(By.CSS_SELECTOR, ".o_app_icon"))
        # If user is not logged in, log in
        if homemenucount < 1:
            driver.find_element(By.XPATH, "//label[contains(.,'Employee')]").click()
            driver.find_element(By.XPATH, "//a[contains(@href,'/web/login')]").click()
            driver.find_element(By.XPATH, "//input[@id='login']").click()
            driver.find_element(By.XPATH, "//input[@id='login']").send_keys("admin")
            driver.find_element(By.XPATH, "//input[@id='password']").click()
            # Password goes here
            adminpw = get_parameters["adminpw"]
            driver.find_element(By.XPATH, "//input[@id='password']").send_keys(adminpw)
            driver.find_element(By.XPATH, "//button[contains(@type,'submit')]").click()
        elif appiconcount > 0:
            # User is already logged in and window was already open
            pass
        else:
            # If user is logged in, go to App menu
            driver.find_element(By.XPATH, "//nav/a").click()

        # Open Sales App
        driver.find_element(By.XPATH, "//a/div[contains(.,'Sales')]").click()
        # Open Pipeline
        driver.find_element(
            By.XPATH,
            "//div[text()='Lead Generation']/../../..//button[text()='Pipeline']",
        ).click()
        # Wait for Loading Message
        WebDriverWait(driver, basetimeout).until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'o_loading')]")
            )
        )
        WebDriverWait(driver, basetimeout).until(
            expected_conditions.invisibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'o_loading')]")
            )
        )
        # Wait for page to load
        WebDriverWait(driver, basetimeout).until(
            expected_conditions.visibility_of_element_located(
                (
                    By.XPATH,
                    "//ol[contains(@class,'breadcrumb')]/li"
                    "[contains(.,'Opportunities')]",
                )
            )
        )
        # Open Kanban view
        driver.find_element(
            By.XPATH, "//button[contains(@data-view-type,'kanban')]"
        ).click()
        # Search for existing record
        driver.find_element(By.CSS_SELECTOR, ".o_searchview_input").click()
        # Wait for Loading Message
        WebDriverWait(driver, basetimeout).until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'o_loading')]")
            )
        )
        WebDriverWait(driver, basetimeout).until(
            expected_conditions.invisibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'o_loading')]")
            )
        )
        # Searchbar
        driver.find_element(By.CSS_SELECTOR, ".o_searchview_input").click()
        driver.find_element(By.CSS_SELECTOR, ".o_searchview_input").send_keys(
            "Eisenhower"
        )
        driver.find_element(By.CSS_SELECTOR, ".o_searchview_input").send_keys(
            Keys.ENTER
        )
        # Wait for Loading Message
        WebDriverWait(driver, basetimeout).until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'o_loading')]")
            )
        )
        WebDriverWait(driver, basetimeout).until(
            expected_conditions.invisibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'o_loading')]")
            )
        )
        # No existing record
        elements = driver.find_elements(By.CSS_SELECTOR, ".o_kanban_record")
        assert len(elements) == 0

        # List view
        driver.find_element(By.XPATH, "//button[contains(@accesskey,'l')]").click()
        # Create new record
        driver.find_element(By.CSS_SELECTOR, ".o_list_button_add").click()
        # Subject
        driver.find_element(
            By.XPATH, "//h1/input[contains(@placeholder, 'e.g. Product Pricing')]"
        ).click()
        driver.find_element(
            By.XPATH, "//h1/input[contains(@placeholder, 'e.g. Product Pricing')]"
        ).send_keys("111 Eisenhowertestttt Ave")
        # Revenue
        driver.find_element(
            By.XPATH, "//label[contains(text(),'Expected Revenue')]/../div/div/input"
        ).click()
        driver.find_element(
            By.XPATH, "//label[contains(text(),'Expected Revenue')]/../div/div/input"
        ).clear()
        driver.find_element(
            By.XPATH, "//label[contains(text(),'Expected Revenue')]/../div/div/input"
        ).send_keys("11000")
        # Billing
        driver.find_element(
            By.XPATH,
            "//label[contains(text(),'Contact for Billing')]/../../td/div/div/input",
        ).click()
        driver.find_element(
            By.XPATH,
            "//label[contains(text(),'Contact for Billing')]/../../td/div/div/input",
        ).send_keys("test")
        driver.find_element(By.LINK_TEXT, "Test").click()
        # Rating
        driver.find_element(By.XPATH, "//a[contains(@title,'High')]").click()
        # Save record
        driver.find_element(By.XPATH, "//button[contains(@accesskey,'s')]").click()

        # Check for Edit button
        WebDriverWait(driver, basetimeout).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, "//button[contains(@accesskey,'a')]")
            )
        )
        # Check name
        WebDriverWait(driver, basetimeout).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, "//h1/span[contains(@class,'o_form_field')]")
            )
        )
        # Check name
        assert (
            driver.find_element(
                By.XPATH, "//h1/span[contains(@class,'o_form_field')]"
            ).text
            == "111 Eisenhower Ave"
        )
