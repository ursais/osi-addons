# Functional Tests using Selenium

## Installation

* Run
```shell script
python3 -m venv env
. env/bin/activate
pip install -r requirements.txt
```
* Download Selenium IDE from the [Selenium website](https://www.selenium.dev/selenium-ide).
  Choose the Chrome or Firefox version based on your web browser of choice

## Configuration

The Selenium tests require a database without previous test data.
If data from previous Selenium tests are found, the tests will fail.

## Writing Tests in IDE

* At the top left, near the run buttons, select the plus (+) sign to create a new test in the project
* At the top right, select the "Rec" button (rec circle) to begin recording a workflow
* A new browser window will open. Selenium will record your actions as you perform each step of the workflow
* When the workflow is complete, return to the Selenium window and select the Stop button (replaces Rec button)
* The Selenium tests require unique identifiers for each webpage element it interacts with.

  * Many of the default Targets selected by the recording will need to be modified to ensure that they are truly unique
  * This typically includes replacing any use of indices (e.g. "//ul[2]")
  * This may require referring to a parent element first, then the desired element by inheritance

* It may be helpful to include assertions during the test to check if things are going well

  * Right click on an existing step and select "Insert new command"
  * See the `Selenium Command API <https://www.selenium.dev/selenium-ide/docs/en/api/commands>`_ for more details

* Save the test when it is complete, and take it for a test run

## Running Tests Manually through IDE

* Click on the Se extension icon in the top right of your browser window
* Select "Open an existing project"
* Select a `.side` file from this directory
* Near the top left of the Selenium popup window, there are two Triangular ("Play") buttons.
  Select the left button with lines to run all tests, or run a test individually with the second button

## Interpreting Results

The log will return a success message if every step is completed.

Any step that fails, whether by a missed assertion or by timeout, will stop the test
with a message in the log explaining which step failed and why.

If an Odoo error occurs at any point, the next step will likely time out because it
cannot find the target element. If this occurs, the test window will remain open with
the Odoo error popup to indicate what went wrong.

## Exporting Tests to Python

* In the Selenium IDE window, click the three dots (...) next to the test name on the left.
* Select Export.
* Choose Python pytest, export the test as a .py file and save it in the `tests` directory.
