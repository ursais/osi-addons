# Install Odoo dependencies

* libffi-dev
* libgeoip-dev
* libjpeg-dev
* libldap2-dev
* libsasl2-dev
* libxml2-dev
* libxslt1-dev
* nginx
* node-less
* postfix
* postgresql
* postgresql-server-dev-9.5
* python-dev
* python-pip
* python-psycopg2
* python-virtualenv
* zlib1g-dev

# Webkit

* Download Webkit from https://github.com/wkhtmltopdf/wkhtmltopdf/releases/tag/0.12.1
* Install Webkit and create a symlink:

`# ln -s /usr/local/bin/wkhtmltopdf /usr/bin/wkhtmltopdf`

# PostgreSQL

* Create a PostgreSQL user for odoo

# Odoo

* Create an Odoo user
* Clone the repository
* Change the ownership of the repo to odoo
* Create the environment

`$ virtualenv env && . env/bin/activate && pip install -r requirements.txt`

* Create /etc/odoo
* Create Odoo config file
* Create Odoo init script
* Create /var/log/odoo
* Create /var/backups/odoo
* Enable and start Odoo

# Nginx

* Create Nginx config file
* Create the SSL directory /etc/nginx/ssl
* Generate the SSL certificate

```
# openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -subj "/C=US/ST=CA/L=Los Angeles/O=IT/CN={{ fqdn }}" \
        -keyout /etc/nginx/ssl/odoo.key \
        -out /etc/nginx/ssl/odoo.crt
```

* Change the permission of the certificate file
* Enable new odoo virtual host
* Enable and start Nginx
