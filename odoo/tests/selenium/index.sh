#!/bin/bash

# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Environment variables - add in Jenkins config
#
#     HOST: URL of odoo machine to run tests
#     DATABASE: name of odoo database to run tests
#     PASSWORD: password of admin user
#     BASETIMEOUT: timeout (in sec) for test lines

# Remove old screenshots in the workspace
rm -f screenshots/*.png || echo "No old screenshots found."

# Run tests
cd tests
DISPLAY=:99
python -m pytest --durations=0 --full-trace -rA --hosturl "$HOST" --dbname "$DATABASE" --adminpw "$PASSWORD" --basetimeout "$BASETIMEOUT"

exit 0
