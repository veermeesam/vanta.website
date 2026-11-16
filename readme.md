# VANTA website draft

A responsive services and portfolio website with a small private inquiry form backend. The request form saves submissions to a local SQLite database and has no public submissions or admin-list page.

## Run a local preview

1. Install Python 3 if it is not already installed.
2. Open a terminal in this folder.
3. Run `python server.py` (on some Windows installations, use `py server.py`).
4. Open `http://127.0.0.1:8000` in your browser.

The server creates `data/vanta_requests.sqlite3` when it starts. Keep the `data` folder private and back it up securely. Do not put it in a public web folder or commit it to a public code repository.

## Before publishing online

This is a local prototype, not a production hosting setup. Before collecting real client information, choose a secure host and database, enable HTTPS, restrict database access, add spam protection and authenticated staff access, and finalize a privacy policy with a contact address and retention period. Never request account passwords, verification codes, recovery codes, or private keys. Account owners must use official account recovery channels.

The portfolio examples are illustrative placeholders; replace them with accurate work examples and get client permission before sharing identifiable details. The listed prices match the supplied image.
