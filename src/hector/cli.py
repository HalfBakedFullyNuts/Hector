"""Administrative CLI for the Hector service.

Usage:
    hector create-admin --email admin@example.com --password Str0ngPass
    hector serve
"""

import argparse
import asyncio
import sys

from sqlalchemy import select

from hector.auth.password import hash_password
from hector.models.user import User, UserRole
from hector.schemas.auth import validate_password_strength


def _build_parser() -> argparse.ArgumentParser:
    """Define the CLI command surface."""
    parser = argparse.ArgumentParser(prog="hector", description="Hector admin tooling")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("serve", help="Run the HTTP API server")

    create_admin = subparsers.add_parser("create-admin", help="Bootstrap an ADMIN account")
    create_admin.add_argument("--email", required=True)
    create_admin.add_argument("--password", required=True)
    return parser


async def _create_admin(email: str, password: str) -> int:
    """Persist a verified active admin; returns a process exit code."""
    from hector.config import get_settings
    from hector.database import close_db, get_session_factory

    get_settings()
    try:
        factory = get_session_factory()
        async with factory() as session:
            existing = await session.execute(select(User).where(User.email == email))
            if existing.scalar_one_or_none() is not None:
                print(f"error: user {email} already exists", file=sys.stderr)  # noqa: T201
                return 1

            session.add(
                User(
                    email=email,
                    hashed_password=hash_password(password),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                )
            )
            await session.commit()
        print(f"created admin: {email}")  # noqa: T201
        return 0
    finally:
        await close_db()


def main(argv: list[str] | None = None) -> int:
    """Dispatch CLI commands; returns the process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    assert args is not None
    if args.command == "create-admin":
        try:
            strong_password = validate_password_strength(args.password)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)  # noqa: T201
            return 2
        return asyncio.run(_create_admin(args.email.lower(), strong_password))

    if args.command == "serve":
        from hector.main import run_server

        run_server()
        return 0

    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
