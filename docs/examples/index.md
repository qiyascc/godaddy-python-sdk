# Recipes

Complete scripts for jobs people use the SDK for. Each one runs as it is once your credentials are set, and each one only uses the public API described in the guides.

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} A subdomain per customer
:link: customer-subdomains
:link-type: doc

Give every new customer `name.example.com`, check that the name is free, and remove it when they leave.
:::

:::{grid-item-card} Dynamic DNS
:link: dynamic-dns
:link-type: doc

Keep `home.example.com` pointed at a connection whose public IP changes.
:::

:::{grid-item-card} Let's Encrypt DNS-01
:link: acme-dns-01
:link-type: doc

Certbot hooks that publish and clean up `_acme-challenge` records, for wildcard certificates.
:::

:::{grid-item-card} Moving between providers
:link: migrate-between-providers
:link-type: doc

Copy a zone from one provider to another with the sibling SDKs.
:::

:::{grid-item-card} Django and FastAPI
:link: web-frameworks
:link-type: doc

Create DNS records from a web application, sync and async.
:::

:::{grid-item-card} Scheduled jobs
:link: scheduled-jobs
:link-type: doc

Run any of these from cron, a systemd timer or the Windows Task Scheduler.
:::
::::

All examples read credentials from the environment (`GODADDY_API_KEY` and `GODADDY_API_SECRET`), so they contain no secrets. Replace `example.com` and the addresses with your own.
