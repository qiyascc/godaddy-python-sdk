# A subdomain per customer

A SaaS product gives each customer an address like `acme.example.com`. All of them point at the same server, and the application decides from the host name which customer is asking. This recipe creates the record at sign up and removes it when the customer leaves.

## The rules

- Customer names are lower case letters, digits and hyphens, 3 to 40 characters, not starting or ending with a hyphen. That is a safe subset of what DNS allows.
- Some names are reserved: `www`, `api`, `mail` and anything else your own services use.
- Creating a name that already exists is an error, so two customers can never share one.
- Removing a name that is already gone is fine.

## The code

```python
import re

from godaddy import GoDaddy

ZONE = "example.com"
SERVER_IP = "203.0.113.10"
RESERVED = {"www", "api", "mail", "admin", "status", "docs"}
VALID = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,38}[a-z0-9])$")


class NameTaken(Exception):
    pass


def check_name(slug: str) -> str:
    slug = slug.strip().lower()
    if not VALID.match(slug) or slug in RESERVED:
        raise ValueError(f"{slug!r} cannot be used as a subdomain")
    return slug


def create_customer_site(gd: GoDaddy, slug: str) -> str:
    slug = check_name(slug)
    if gd.dns.exists(ZONE, "A", slug):
        raise NameTaken(f"{slug}.{ZONE} is already taken")
    gd.dns.point(ZONE, slug, SERVER_IP)
    return f"{slug}.{ZONE}"


def remove_customer_site(gd: GoDaddy, slug: str) -> None:
    gd.dns.unpoint(ZONE, check_name(slug))


if __name__ == "__main__":
    with GoDaddy() as gd:
        print(create_customer_site(gd, "acme"))
```

## How it works

1. `check_name` refuses anything that is not a plain label, before a request is made.
2. `dns.exists` asks GoDaddy whether an `A` record with that name is already there.
3. `dns.point` creates it. It sends one `PUT` for that type and name, so nothing else in the zone is touched.
4. `dns.unpoint` removes the `A` record and does nothing if it is already gone, so cancelling twice is harmless.

Between `exists` and `point` another process could claim the same name. If sign ups can race, make the name unique in your database first (a unique column), and only then create the record. The database decides who gets the name, DNS just follows.

## A wildcard instead?

A single `*` record (`*.example.com`) answers for every name, with no API call per customer. It is simpler, but every name resolves, including ones nobody owns, and you cannot point one customer at a different server. Per customer records are the better fit when customers can bring their own server or when you want unused names to fail.

## Serving the subdomains

DNS only gets the visitor to your server. The web server and the TLS certificate must accept the new name too:

- With a wildcard certificate for `*.example.com`, every customer name is covered at once. [](acme-dns-01.md) shows how to get one from Let's Encrypt with this SDK.
- In Django, add `.example.com` (with the leading dot) to `ALLOWED_HOSTS`.
