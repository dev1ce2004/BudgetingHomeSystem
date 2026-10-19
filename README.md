# BudgetingHomeSystem

A self-hosted household budgeting app that runs entirely on your home network. A Windows PC acts as the hub and stores all data, and family members use it from their Android phones as an installable PWA that keeps working offline. No cloud, no external server.

## Features

- Shared overview of income, expenses and transfers between accounts
- Categories, accounts and a monthly spending limit
- Multiple household members with personal access keys, plus access revocation
- **Offline-first PWA:** entries made without Wi-Fi are queued and synced when the hub is reachable again
- **Safe sync:** idempotent operations prevent duplicates, and version checks detect conflicting edits instead of silently overwriting them
- Permissions: everyone sees all transactions, members edit their own, the admin edits everything
- Automatic hourly SQLite backups and JSON export
- HTTPS on the LAN via an auto-generated local certificate authority

## Tech Stack

- **Backend:** Python (standard library HTTP server), SQLite
- **Frontend:** vanilla JavaScript PWA with a service worker
- **Security:** TLS with a self-generated local CA (`cryptography`), bearer-token auth

## Quick Start (Windows)

1. Install Python 3.10+ from python.org.
2. Run `Instaliraj.bat` to create a virtual environment and install dependencies.
3. Run `Pokreni.bat --ip <your-PC-LAN-IP>` and keep the window open.
4. Install `data\BudgetingHomeSystem-CA.crt` under **Current User → Trusted Root Certification Authorities**.
5. Run `Otvori-hub.bat` to open the admin dashboard.

To connect a phone, add a member under **Settings**, install the same CA certificate on the phone as a CA certificate, and open the member's link in Chrome on the home Wi-Fi.

Detailed setup, backup restore and known limitations are in [UPUTE.md](UPUTE.md) (Croatian).

## Tests

```
python -m unittest discover -s tests -v
```
