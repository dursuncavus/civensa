#!/usr/bin/env python3
"""Print catalog evidence in a READ ONLY transaction; never print the connection URL."""
import argparse
import json
import os
from pathlib import Path
import sys

from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db_privileges import audit_engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url-env', default='DATABASE_URL', help='Environment variable holding the URL (default: DATABASE_URL)')
    args = parser.parse_args()
    engine = None
    try:
        url = os.environ[args.url_env]
        for prefix in ('postgres://', 'postgresql://'):
            if url.startswith(prefix):
                url = 'postgresql+psycopg://' + url[len(prefix):]
        engine = create_engine(url, hide_parameters=True)
        snapshot = audit_engine(engine)
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        return 0
    except Exception:
        print('Database privilege audit failed; check URL variable, connectivity and PostgreSQL 16+. Connection details suppressed.', file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == '__main__':
    sys.exit(main())
