# OnLogic GraphQL integration

_NOTE:_ For Odoo v17, we have copied the OCA module `graphql_base`
from https://github.com/OCA/rest-framework.git with branch (17.0) into `onlogic-addons/graphql_base`

The rest framework OCA module has not been officially migrated to version 17 yet so we are currently hosting it in `onlogic-addons`

# How to expose a new Odoo record via GraphQL

1. Add a new directory under ol_graphql/schema
   - The name of the directory should be the `table` name of the given Odoo record
2. Add the necessary files to the directory
   - `types.py` defining all of the data this GraphQL object should have
   - `queries.py` (optional) Only create this file if you want to make this object directly a queriable
   - `mutations.py` (optional) Only create this file if you want allow update/creation of these objects trough GraphQL
3. `DO NOT` create any other "random" directory under `ol_graphql/schema` as it will cause an error in `ol_graphql/schema/loader.py`

## GraphQL resources

Intro to GraphQL: https://graphql.org/learn/
Python library: https://docs.graphene-python.org/en/latest/
OCA Demo module: https://github.com/OCA/rest-framework/tree/12.0/graphql_demo
