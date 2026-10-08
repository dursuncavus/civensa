# Historical staging QA scripts

Preserved byte-for-byte from staging b3a4ad1. These scripts assume legacy pilot
accounts, periods, migration heads, version labels and login redirects. Some
change passwords, accounts, imports or persisted values. They are historical
manual references, NOT current release gates; do not run against production.

Current supported validation is `python -m pytest -q --require-postgres` with
`CIVENSA_TEST_POSTGRES_URL` pointing to a fresh disposable PostgreSQL database.
Use `python check_bundle.py` for the current source/package integrity check.
Migrate any needed historical scenario to current fixtures before running it.
