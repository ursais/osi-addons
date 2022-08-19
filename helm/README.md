# Odoo Deployment

## Table of Contents
* [Development environment](#Development-environment)
* [Test environment](#Test-environment)
* [QA environment](#QA-environment)
* [Production environment](#Production-environment)
* [Secrets](#Secrets)
* [Release](#Release)
* [Known issues](#Known-issues)

## Development environment

Create the project:
```shell script
kubectl create namespace odoo-dev
```
Edit the variables in helm/odoo/values.yaml

Run
```shell script
helm dependency update helm/odoo
helm upgrade --install odoo helm/odoo
```

## Test environment

Create the project:
```shell script
kubectl create namespace odoo-test
```
Edit the variables in helm/odoo/values.test.yaml

Run
```shell script
helm upgrade --install odoo -f helm/odoo/values.test.yaml helm/odoo
```

## QA environment

Create the project:
```shell script
kubectl create namespace odoo-qa
```
Edit the variables in helm/odoo/values.qa.yaml

Run
```shell script
helm upgrade --install odoo -f helm/odoo/values.qa.yaml helm/odoo
```

## Production environment

Create the project:
```shell script
kubectl create namespace odoo
```
Edit the variables in helm/odoo/values.production.yaml

Run
```shell script
helm upgrade --install odoo -f helm/odoo/values.production.yaml helm/odoo
```

## Secrets

The installation generates random values for confidential information like passwords,
tokens, keys, etc. You need to replace them with the value from the provider.

### External database

```shell
SECRET=`echo -n "PASSWORD" | base64`
kubectl edit secret odoo-externaldb
  data:
    db-password: $SECRET
```

### Storage

```shell
SECRET1=`echo -n "Account URL" | base64`
SECRET2=`echo -n "Connection string" | base64`
kubectl edit secret odoo
  data:
    azure-storage-account-url: $SECRET1
    azure-storage-connection-string: $SECRET2
```

## Release

Create a new release in the repository:
https://github.com/ursais/odoo-template/releases

Update the deployment:
```shell script
TAG=20210527
NAMESPACE=odoo-test
kubectl set image deploy odoo \
    odoo=docker.pkg.github.com/ursais/odoo-template/odoo-template:$TAG \
    --namespace $NAMESPACE
```

## Backup

Install Velero:
```shell
export BUCKET=velerobackup-<name>
export REGION=us-east-2
velero install \
    --provider aws \
    --use-restic \
    --plugins velero/velero-plugin-for-aws:v1.2.0 \
    --bucket $BUCKET \
    --backup-location-config region=$REGION \
    --snapshot-location-config region=$REGION \
    --secret-file ./helm/credentials-velero
```

Create schedules:
```shell
velero create schedule full-daily --schedule="@every 24h"
velero create schedule odoo-daily --schedule="@every 24h" --include-namespaces <name>-odoo
velero create schedule odoo-qa-daily --schedule="@every 24h" --include-namespaces <name>-odoo-qa
velero create schedule odoo-test-daily --schedule="@every 24h" --include-namespaces <name>-odoo-test
velero create schedule odoo-dev-daily --schedule="@every 24h" --include-namespaces <name>-odoo-dev
```

## Known issues

* https://github.com/bitnami/charts/issues/6121
  Upgrading the PostgreSQL helm chart regenerates the password in the secret and causes
  Odoo's connections to fail.
