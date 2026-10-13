import sys

from godaddy import GoDaddy, NotFoundError


def main() -> None:
    if len(sys.argv) != 4:
        print("usage: python subdomain.py <domain> <name> <ip>")
        sys.exit(1)

    domain, name, ip = sys.argv[1:]
    with GoDaddy() as gd:
        try:
            current = gd.dns.list(domain, "A", name)
        except NotFoundError:
            print(f"{domain} is not in this GoDaddy account")
            sys.exit(1)

        if any(record.data == ip for record in current):
            print(f"{name}.{domain} already points to {ip}")
            return

        gd.dns.point(domain, name, ip)
        print(f"{name}.{domain} now points to {ip}")


if __name__ == "__main__":
    main()
