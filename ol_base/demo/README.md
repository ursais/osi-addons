# OnLogic Demo Data #

## Accounting Demo Data ##

The chart of accounts is tricky. Here's how it works:

1. Define a `account.chart.template` object
2. Define any accounts you want in that template. Here we do that with a csv file for easier editing.
   If you need to update the accounts, use a spreadsheet app to do it
3. Load the chart (as long as no accounting moves have been created). The core code installs a
   generic chart of accounts, so we call a separate function to make sure our chart is loaded.
   This function is called once for each company, so that they each have the same accounts.
