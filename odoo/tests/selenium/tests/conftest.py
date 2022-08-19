# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from datetime import datetime

import pytest
from selenium import webdriver


def pytest_addoption(parser):
    # Collect parameters from console call
    parser.addoption("--hosturl", action="store")
    parser.addoption("--dbname", action="store")
    parser.addoption("--adminpw", action="store")
    parser.addoption("--basetimeout", action="store")


@pytest.fixture(scope="session")
def get_parameters(request):
    strdict = {
        "hosturl": request.config.option.hosturl,
        "dbname": request.config.option.dbname,
        "adminpw": request.config.option.adminpw,
        "basetimeout": int(request.config.option.basetimeout),
    }
    return strdict


@pytest.fixture(scope="function")
def setup_hostpage(get_parameters):
    # At beginning of test: open host homepage
    chrops = webdriver.ChromeOptions()
    chrops.add_argument("headless")
    chrops.add_argument("disable-gpu")
    chrops.add_argument("disable-popup-blocking")

    caps = webdriver.DesiredCapabilities.CHROME.copy()
    caps["acceptSslCerts"] = True
    caps["acceptInsecureCerts"] = True

    driver = webdriver.Chrome(options=chrops, desired_capabilities=caps)

    hosturl = get_parameters["hosturl"]
    dbname = get_parameters["dbname"]
    fullurl = "https://{}/web?db={}".format(hosturl, dbname)
    # If host wasn't prefixed with http(s):// we do it here
    if not fullurl[:4] == "http":
        httpurl = "http://" + fullurl
        driver.get(httpurl)
    else:
        driver.get(fullurl)

    # Set window size and timeout
    driver.set_window_size(1200, 800)
    driver.implicitly_wait(get_parameters["basetimeout"])

    yield driver

    # Save a screenshot
    fname = (
        os.path.dirname(os.path.abspath(__file__))[:-5]
        + "screenshots/"
        + datetime.now().strftime("%Y%m%d%H%M%S%f")
        + ".png"
    )
    driver.save_screenshot(fname)

    driver.quit()
