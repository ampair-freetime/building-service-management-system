"""Start the same bounded backend with or without Docker."""

import argparse
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--limit-concurrency", type=int, default=16)
    parser.add_argument("--migrate", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or args.limit_concurrency < 2:
        parser.error("port must be 1..65535 and limit-concurrency must be at least 2")

    # Validate configuration before connecting to the database or serving traffic.
    import uvicorn

    from app.core.config import get_settings

    get_settings()
    if args.migrate:
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=BACKEND_DIR,
            check=True,
        )
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        workers=1,
        reload=False,
        limit_concurrency=args.limit_concurrency,
        timeout_keep_alive=5,
        log_level="info",
    )


if __name__ == "__main__":
    main()
