# Performance Tests with Locust

## Installation

```shell script
python3 -m venv env
. env/bin/activate
pip install -r requirements.txt
```

## Running the tests

* Edit `locust.conf` to your needs
* Run
```shell script
export ODOO_DB_NAME=Test
export ODOO_LOGIN=admin
export ODOO_PASSWORD=admin
locust --config=locust.conf
```
* Go to http://localhost:8089

## Advanced topics

It is possible to set the weight of the users (CRMUser, SaleUser, ProjectUser,
PurchaseUser, AccountUser, StockUser) by editing the values in `locustfile.py`.

You can also run specific user, for example:
```shell script
locust --config=locust.conf SaleUser
```
