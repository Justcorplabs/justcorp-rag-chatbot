"""Inert PostgreSQL settings. No drivers, engines, schemas, or network access.

Future database-dependent operations must call load_database_settings first.
This module deliberately does not load dotenv or instantiate global settings.
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Mapping
from ipaddress import IPv6Address
from urllib.parse import quote, unquote


class DatabaseConfigurationError(ValueError):
    """Diagnostics contain fixed messages only, never supplied values."""


@dataclass(frozen=True, slots=True, repr=False)
class DatabaseURI:
    """Validated components; future SQLAlchemy integration must use URL.create.

    Pass these decoded fields directly, without parsing or decoding again.
    render_as_string is for explicit export only; default output hides credentials.
    """
    drivername: str
    username: str = field(repr=False)
    password: str | None = field(repr=False)
    host: str
    port: int | None
    database: str

    def __repr__(self):
        return "DatabaseURI(<redacted>)"

    def render_as_string(self, hide_password=True):
        user = quote(self.username, safe="")
        if self.password is not None:
            user += ":" + ("***" if hide_password else quote(self.password, safe=""))
        host = "[" + self.host + "]" if ":" in self.host else self.host
        port = "" if self.port is None else ":" + str(self.port)
        return self.drivername + "://" + user + "@" + host + port + "/" + self.database


def _parse_uri(uri):
    # Subset of SQLAlchemy 2.0.44 engine/url.py::_parse_url. Only credentials
    # are percent-decoded by that parser. Exclude delimiter ambiguity entirely.
    credential = r"(?:[A-Za-z0-9_.~-]|%[0-9A-Fa-f]{2})"
    match = re.fullmatch(
        r"postgresql\+psycopg://(?P<username>" + credential + r"+)"
        r"(?::(?P<password>" + credential + r"*))?@"
        r"(?P<host>\[[:0-9a-f]+\]|[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?)"
        r"(?::(?P<port>[1-9][0-9]{0,4}))?/(?P<database>[A-Za-z0-9_-]+)", uri)
    if match is None:
        raise DatabaseConfigurationError("Invalid PostgreSQL psycopg URI")
    parts = match.groupdict()
    try:
        for key in ("username", "password"):
            if parts[key] is not None:
                parts[key] = unquote(parts[key], encoding="utf-8", errors="strict")
                if any(ord(c) < 32 or ord(c) == 127 for c in parts[key]):
                    raise ValueError
        host = parts["host"]
        if host.startswith("["):
            host = host[1:-1]
            if str(IPv6Address(host)) != host:
                raise ValueError
        elif any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                 for label in host.split(".")) or len(host) > 253:
            raise ValueError
        port = int(parts["port"]) if parts["port"] is not None else None
        if port is not None and port > 65535:
            raise ValueError
    except (ValueError, UnicodeError):
        raise DatabaseConfigurationError("Invalid PostgreSQL psycopg URI") from None
    return DatabaseURI("postgresql+psycopg", parts["username"], parts["password"],
                       host, port, parts["database"])


@dataclass(frozen=True, slots=True, repr=False)
class DatabaseSettings:
    environment: str
    uri: DatabaseURI = field(repr=False)
    sslmode: str
    sslrootcert: str = field(repr=False)
    connect_timeout: int
    pool_size: int
    pool_timeout: int
    max_overflow: int = field(default=0, init=False)

    def __repr__(self):
        return "DatabaseSettings(<redacted>)"


def load_database_settings(environ: Mapping[str, str] | None = None) -> DatabaseSettings:
    """Validate on demand; only backend environment values are consulted.

    An injected mapping supports isolated tests. No filesystem dotenv discovery.
    Credentials remain sensitive: never serialize settings or log attributes.
    """
    env = os.environ if environ is None else environ
    environment = env.get("DATABASE_ENVIRONMENT", "development")
    if environment not in {"development", "test", "production"}:
        raise DatabaseConfigurationError("Invalid DATABASE_ENVIRONMENT")
    uri = env.get("DATABASE_URL", "")
    if not uri:
        raise DatabaseConfigurationError("DATABASE_URL is required for database operations")
    connection = _parse_uri(uri)

    def integer(name, default, upper):
        value = env.get(name, str(default))
        if not re.fullmatch(r"[0-9]{1,3}", value) or not 1 <= int(value) <= upper:
            raise DatabaseConfigurationError("Invalid " + name)
        return int(value)

    connect_timeout = integer("DATABASE_CONNECT_TIMEOUT", 5, 30)
    pool_size = integer("DATABASE_POOL_SIZE", 2, 5)
    pool_timeout = integer("DATABASE_POOL_TIMEOUT", 5, 30)
    sslmode = env.get("DATABASE_SSLMODE", "verify-full")
    rootcert = env.get("DATABASE_SSLROOTCERT", "")
    if sslmode not in {"disable", "verify-full"}:
        raise DatabaseConfigurationError("Invalid DATABASE_SSLMODE")
    if environment == "production" and sslmode != "verify-full":
        raise DatabaseConfigurationError("Production requires TLS verify-full")
    if sslmode == "disable" and connection.host not in {"localhost", "127.0.0.1", "::1"}:
        raise DatabaseConfigurationError("TLS may only be disabled for local development or test")
    if sslmode == "verify-full":
        try:
            usable = bool(rootcert) and Path(rootcert).is_absolute() and Path(rootcert).is_file()
            if usable:
                with Path(rootcert).open("rb") as certificate:
                    usable = bool(certificate.read(1))
        except (OSError, ValueError):
            usable = False
        if not usable:
            raise DatabaseConfigurationError("TLS requires a readable absolute CA certificate file") from None
    return DatabaseSettings(environment, connection, sslmode, rootcert,
                            connect_timeout, pool_size, pool_timeout)
