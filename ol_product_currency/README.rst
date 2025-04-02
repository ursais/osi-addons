========================
Onlogic Product Currency
========================

The product template currency_id is computed based on the assigned company or
the base.main_company or first company it finds.

The purpose of this module is to changes the product template currency_id
compute method to function as the cost_currency_id which first looks at the
assigned company but then the logged in company.
