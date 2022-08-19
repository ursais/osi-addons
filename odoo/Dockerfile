FROM ursa/odoo-15.0:latest
MAINTAINER Open Source Integrators <support@opensourceintegrators.com>

# Copy files
COPY --chown=odoo setup.py /odoo/
COPY --chown=odoo migration.yml /odoo/
COPY --chown=odoo requirements.txt /odoo/
COPY --chown=odoo songs /odoo/songs

# Copy Odoo
COPY --chown=odoo odoo /odoo/odoo/
# Copy Addons
# COPY src/paid-addons /odoo/addons/
COPY --chown=odoo src/private-addons /odoo/addons/
# COPY src/enterprise /odoo/addons/

RUN cd /odoo && pip3 install -r requirements.txt
