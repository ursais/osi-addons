On the **Product Template form > Time Based pricing tab**, use the **Populate Recurrence Prices** field to set the recurrence periods to be used.
For each recurrence period selected, a price factor can be provided (default is 1).
This factor will be used to find the price for that period. For example, it can be used to apply discounts for larger periods.

Example:

+-------------+---------+
| Recurrence  | Factor  |
+=============+=========+
| Yearly      | 1.0     |
| Three Years | 0.9     |
+-------------+---------+

When the **Populate Recurrence Prices** field is set, the Time Based Pricing" will be automatically populated, computing the price for each Variant/Recurrence period combination, considering:

* The Product Template public sales price
* Each Variant Attribute extra price
* The Recurrence Period factor
