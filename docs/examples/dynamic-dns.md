# Dynamic DNS

A home server, a small office or a Raspberry Pi often sits behind a connection whose public IP address changes from time to time. This script keeps `home.example.com` pointed at whatever the current address is. Run it every few minutes and the name follows the connection.

## The script

Save it as `ddns.py`:

```python
import sys

import httpx

from godaddy import GoDaddy, GoDaddyError

ZONE = "example.com"
NAME = "home"
TTL = 600
IP_SERVICES = ["https://api.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"]


def public_ip() -> str:
    for url in IP_SERVICES:
        try:
            answer = httpx.get(url, timeout=10).text.strip()
        except httpx.HTTPError:
            continue
        if answer:
            return answer
    raise RuntimeError("could not find the public IP address")


def main() -> int:
    ip = public_ip()
    try:
        with GoDaddy() as gd:
            current = [r.data for r in gd.dns.list(ZONE, "A", NAME)]
            if current == [ip]:
                print(f"{NAME}.{ZONE} already points to {ip}")
                return 0
            gd.dns.point(ZONE, NAME, ip, ttl=TTL)
    except GoDaddyError as exc:
        print(f"GoDaddy error: {exc}", file=sys.stderr)
        return 1
    print(f"{NAME}.{ZONE}: {current or 'no record'} -> {ip}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Why it is written this way

- **It reads before it writes.** Most runs find nothing to change, so they cost one read request and no write. That keeps you far from GoDaddy's rate limits even if the script runs every minute.
- **It asks more than one service for the IP.** If one is down, the next one answers. Each of them returns the address as plain text.
- **It uses a short TTL.** When the address changes, resolvers forget the old one quickly.
- **It returns an exit code.** `0` on success, `1` on an API error, so cron or systemd can tell that something went wrong.

## Run it

```bash
export GODADDY_API_KEY=your-key
export GODADDY_API_SECRET=your-secret
python ddns.py
```

```text
home.example.com: no record -> 198.51.100.23
```

Then schedule it every five minutes, see [](scheduled-jobs.md).

## IPv6

If the connection also has a public IPv6 address, ask a service that answers over IPv6 and point the same name at it. `point` sees the IPv6 address and writes an `AAAA` record next to the `A` record:

```python
answer = httpx.get("https://api6.ipify.org", timeout=10).text.strip()
gd.dns.point(ZONE, NAME, answer, ttl=TTL)
```

To check the current value, read `"AAAA"` records instead of `"A"`.
