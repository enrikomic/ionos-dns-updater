"""
IONOS DNS Updater — pyscript integration for Home Assistant.

Exposes a service: pyscript.update_ionos_dns

Service parameters:
  ip      (optional) — IPv4 address to set. Auto-detected if omitted.
  dry_run (optional) — If true, only log current records without updating.

Setup in configuration.yaml:
    pyscript:
      allow_all_imports: true
      apps:
        ionos_dns_updater:
          api_key: "your_prefix.your_secret"
          domain: "your-domain.tld"

File location: <config>/pyscript/ionos_dns_updater.py
"""

import json
import urllib.request
import urllib.error

BASE_URL = "https://api.hosting.ionos.com/dns/v1"


@pyscript_executor
def _get_public_ip():
    for svc in ["https://api.ipify.org", "https://icanhazip.com", "https://checkip.amazonaws.com"]:
        try:
            with urllib.request.urlopen(svc, timeout=5) as resp:
                return resp.read().decode().strip()
        except Exception:
            continue
    raise RuntimeError("Could not detect public IP from any service")


@pyscript_executor
def _api_request(method, path, api_key, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {e.read().decode(errors='replace')}")


@service
async def update_ionos_dns(ip=None, dry_run=False):
    """Update all A records for the configured domain on IONOS."""
    cfg = pyscript.config.get("apps", {}).get("ionos_dns_updater", {})
    api_key = cfg.get("api_key")
    domain = cfg.get("domain")

    if not api_key or not domain:
        log.error("ionos_dns_updater: api_key and domain must be set in configuration.yaml")
        return

    try:
        # Resolve IP
        if ip is None:
            ip = await _get_public_ip()
            log.info(f"ionos_dns_updater: detected public IP {ip}")

        # Validate IPv4
        parts = ip.split(".")
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            log.error(f"ionos_dns_updater: invalid IPv4 address: {ip}")
            return

        # Find zone
        zones = await _api_request("GET", "/zones", api_key)
        zone = next((z for z in zones if z.get("name") == domain), None)
        if zone is None:
            log.error(f"ionos_dns_updater: zone '{domain}' not found")
            return
        log.info(f"ionos_dns_updater: found zone {domain} (id={zone['id']})")

        # Get A records
        zone_data = await _api_request("GET", f"/zones/{zone['id']}?recordType=A", api_key)
        records = zone_data.get("records", [])
        log.info(f"ionos_dns_updater: found {len(records)} A record(s)")

        for rec in records:
            log.info(f"ionos_dns_updater:   {rec['name']} -> {rec['content']}")

        if dry_run:
            log.info("ionos_dns_updater: dry_run=true, no changes made")
            return

        # Build patch payload (one entry per unique name)
        seen = {}
        for rec in records:
            if rec["name"] not in seen:
                seen[rec["name"]] = {
                    "name": rec["name"],
                    "type": "A",
                    "content": ip,
                    "ttl": rec.get("ttl", 3600),
                    "prio": rec.get("prio", 0),
                    "disabled": rec.get("disabled", False),
                }

        await _api_request("PATCH", f"/zones/{zone['id']}", api_key, list(seen.values()))
        log.info(f"ionos_dns_updater: updated {len(seen)} record(s) to {ip}")
        for name in seen:
            log.info(f"ionos_dns_updater:   {name} -> {ip}")

    except Exception as e:
        log.error(f"ionos_dns_updater: {e}")
