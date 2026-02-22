# IONOS DNS Updater

Updates all DNS A records for a domain (and its subdomains) hosted on IONOS, using the [IONOS Developer DNS API](https://developer.hosting.ionos.com/docs/dns).

Exposed as a **Home Assistant pyscript service**.

---

## Requirements

- Python 3.8+
- An [IONOS API key](https://developer.hosting.ionos.com/keys)
- No external Python dependencies (standard library only)
- [pyscript integration](https://github.com/custom-components/pyscript) for Home Assistant

---

## Setup

1. Install the [pyscript integration](https://github.com/custom-components/pyscript) via HACS
2. Copy `update_dns.py` to `<ha_config>/pyscript/ionos_dns_updater.py`
3. Add the following to `configuration.yaml`:

```yaml
pyscript:
  allow_all_imports: true
  apps:
    ionos_dns_updater:
      api_key: "your_prefix.your_secret"
      domain: "your-domain.tld"
```

4. Restart Home Assistant

Your API key is composed of a **prefix** and a **secret** separated by a dot.
Generate one at: https://developer.hosting.ionos.com/keys

---

## Usage

Call the service from **Developer Tools → Services** or in an automation:

```yaml
# Auto-detect public IP and update
service: pyscript.update_ionos_dns

# Set a specific IP
service: pyscript.update_ionos_dns
data:
  ip: "1.2.3.4"

# Dry run — logs current records without changing anything
service: pyscript.update_ionos_dns
data:
  dry_run: true
```

### Automation example — update every hour

```yaml
automation:
  alias: "IONOS DNS — keep IP up to date"
  trigger:
    - platform: time_pattern
      hours: "/1"
  action:
    - service: pyscript.update_ionos_dns
```

Logs are available in the Home Assistant log under `homeassistant.components.pyscript`.

---

## About

This project was fully generated with AI using [Claude Code](https://claude.ai/claude-code) (Anthropic). The code, configuration, and documentation were produced through a conversational session with Claude Sonnet — no code was written manually.

---

## File structure

```
ionos-dns-updater/
├── update_dns.py   # pyscript service
├── .gitignore
└── README.md
```
