# About

The GoDaddy Python SDK is written and maintained by **Qiyas Sadıqov**. More projects by the same author, including the other SDKs and Django packages, are on [theqiyas.cc](https://theqiyas.cc).

## Links

- Documentation: [godaddy-python-sdk.readthedocs.io](https://godaddy-python-sdk.readthedocs.io/en/latest/)
- Source code: [github.com/qiyascc/godaddy-python-sdk](https://github.com/qiyascc/godaddy-python-sdk)
- PyPI: [pypi.org/project/godaddy-python-sdk](https://pypi.org/project/godaddy-python-sdk/)
- Project page: [theqiyas.cc/projects/godaddy-python-sdk](https://theqiyas.cc/projects/godaddy-python-sdk/)
- Issues: [github.com/qiyascc/godaddy-python-sdk/issues](https://github.com/qiyascc/godaddy-python-sdk/issues)

## The DNS SDK family

Four SDKs share the same shape, so code written for one reads the same with the others. `dns.list`, `dns.exists`, `dns.add`, `dns.replace`, `dns.point`, `dns.unpoint`, `dns.alias` and `dns.set_txt` exist in all of them, with the domain first and names relative to it.

| Provider | Package | Import | Docs |
| --- | --- | --- | --- |
| GoDaddy | `godaddy-python-sdk` | `godaddy` | [godaddy-python-sdk.readthedocs.io](https://godaddy-python-sdk.readthedocs.io/en/latest/) |
| Namecheap | `namecheap-python-sdk` | `namecheap_sdk` | [namecheap-python-sdk.readthedocs.io](https://namecheap-python-sdk.readthedocs.io/en/latest/) |
| Hostinger | `hostinger-python-sdk` | `hostinger_sdk` | [hostinger-python-sdk.readthedocs.io](https://hostinger-python-sdk.readthedocs.io/en/latest/) |
| DigitalOcean | `digitalocean-python-sdk` | `digitalocean_sdk` | [digitalocean-python-sdk.readthedocs.io](https://digitalocean-python-sdk.readthedocs.io/en/latest/) |

[](examples/migrate-between-providers.md) shows how to use two of them together.

## License

MIT. You can use the SDK in commercial and private projects. The full text is in the [LICENSE](https://github.com/qiyascc/godaddy-python-sdk/blob/main/LICENSE) file.

GoDaddy is a trademark of its owner. This is an independent project and is not made or endorsed by GoDaddy.
