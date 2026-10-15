"""Synthetic, offline checks for the SEC03-02A configuration boundary."""
import builtins
import importlib
from pathlib import Path
import sys
import re
from urllib.parse import unquote
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database_config import DatabaseConfigurationError, load_database_settings
from test_optional_routes import application


def local(**overrides):
    values = {"DATABASE_URL": "postgresql+psycopg://fixture@localhost/fixture",
              "DATABASE_SSLMODE": "disable"}
    values.update(overrides)
    return values


class DatabaseConfigurationTests(unittest.TestCase):
    def test_missing_and_environment(self):
        with self.assertRaises(DatabaseConfigurationError):
            load_database_settings({})
        for value in ("", "prod", "PRODUCTION", "unknown"):
            with self.subTest(value=value), self.assertRaises(DatabaseConfigurationError):
                load_database_settings(local(DATABASE_ENVIRONMENT=value))

    def test_local_defaults_and_explicit_test(self):
        for environment in ("development", "test"):
            settings = load_database_settings(local(DATABASE_ENVIRONMENT=environment))
            self.assertEqual(settings.environment, environment)
            self.assertEqual((settings.connect_timeout, settings.pool_size,
                              settings.pool_timeout, settings.max_overflow), (5, 2, 5, 0))
        for host in ("127.0.0.1", "[::1]"):
            load_database_settings(local(DATABASE_URL=f"postgresql+psycopg://fixture@{host}/fixture"))
        with self.assertRaises(DatabaseConfigurationError):
            load_database_settings(local(DATABASE_URL="postgresql+psycopg://fixture@remote.invalid/fixture"))

    def test_uri_validation(self):
        for uri in ("sqlite:///fixture", "mysql://localhost/fixture",
                    "postgresql://fixture@localhost/fixture", "postgresql+psycopg2://fixture@localhost/fixture",
                    "postgresql+psycopg://fixture@localhost:0/fixture",
                    "postgresql+psycopg://fixture@localhost:bad/fixture",
                    "postgresql+psycopg://fixture@[bad/fixture",
                    "postgresql+psycopg://fixture@localhost/", "postgresql+psycopg:///fixture",
                    "postgresql+psycopg://localhost/fixture",
                    "postgresql+psycopg://fixture@localhost/fixture?sslmode=disable",
                    "postgresql+psycopg://fixture@localhost/fixture#fragment",
                    "postgresql+psycopg://fixture@localhost/fixture\n",
                    "postgresql+psycopg://fixture%xx@localhost/fixture"):
            with self.subTest(uri=uri), self.assertRaises(DatabaseConfigurationError):
                load_database_settings(local(DATABASE_URL=uri))

    def test_authority_regressions(self):
        authorities = (
            "fixture@remote.invalid@localhost", "fixture:pass@remote.invalid@localhost",
            "fixture@remote.invalid:5432@localhost", "fixture@@localhost",
            "fixture@localhost:", "fixture@[::1]:", "fixture@localhost:65536",
            "fixture@localhost:-1", "fixture@localhost:00001", "@localhost",
            "fixture@", "fixture%00@localhost", "fixture:abc%00@localhost",
            "fixture@local%00host", "fixture@localhost%00", "fixture@localhost,remote.invalid",
            "fixture@localhost\\remote.invalid", "fixture@[::1]remote.invalid",
            "fixture@localhost.", "fixture@127.1", "fixture%FF@localhost",
            "fixture%@localhost", "fixture%0@localhost", "fixture%GG@localhost",
        )
        # 127.1 is syntactically clear but never eligible for local plaintext.
        uris = ["postgresql+psycopg://" + a + "/fixture" for a in authorities]
        uris += ["POSTGRESQL+PSYCOPG://fixture@localhost/fixture",
                 "Postgresql+psycopg://fixture@localhost/fixture"]
        uris += [local()["DATABASE_URL"] + suffix for suffix in (
            "?sslmode=invalid", "?sslmode=verify-full&sslmode=disable",
            "?host=remote.invalid", "?sslrootcert=other", "?connect_timeout=0",
            "?", "#", "%00")]
        for index, uri in enumerate(uris):
            with self.subTest(case=index), self.assertRaises(DatabaseConfigurationError) as error:
                load_database_settings(local(DATABASE_URL=uri))
            self.assertEqual(str(error.exception) in {
                "Invalid PostgreSQL psycopg URI",
                "TLS may only be disabled for local development or test"}, True)
            self.assertIsNone(error.exception.__cause__)

    def accepted_cases(self):
        # Expected decoded components, independently specified; no real credentials.
        password = "p" + "@:/?#%+ "
        encoded = "p%40%3A%2F%3F%23%25%2B%20"
        for host, authority, port in (("localhost", "localhost", None),
                                      ("127.0.0.1", "127.0.0.1:5432", 5432),
                                      ("::1", "[::1]:5432", 5432),
                                      ("db.example.invalid", "db.example.invalid:6543", 6543)):
            for credentials, user, secret in (("fixture", "fixture", None),
                                               ("fixture:", "fixture", ""),
                                               ("fixture%40name:" + encoded,
                                                "fixture@name", password)):
                uri = "postgresql+psycopg://" + credentials + "@" + authority + "/fixture"
                yield uri, ("postgresql+psycopg", user, secret, host, port, "fixture")

    def test_accepted_components_and_pinned_parser_contract(self):
        # SQLAlchemy rel_2_0_44/lib/sqlalchemy/engine/url.py::_parse_url grammar.
        # Source contract check only, NOT execution of SQLAlchemy or its driver.
        grammar = re.compile(
            r"(?P<drivername>[\w+]+)://(?:(?P<username>[^:/]*)"
            r"(?::(?P<password>[^@]*))?@)?(?:"
            r"(?:\[(?P<ipv6>[^/\?]+)\]|(?P<ipv4>[^/:\?]+))?"
            r"(?::(?P<port>[^/\?]*))?)?(?:/(?P<database>[^\?]*))?"
            r"(?:\?(?P<query>.*))?")
        with tempfile.TemporaryDirectory() as directory:
            cert = Path(directory) / "fixture.pem"
            cert.write_text("synthetic CA placeholder", encoding="utf-8")
            for index, (uri, expected) in enumerate(self.accepted_cases()):
                with self.subTest(case=index):
                    settings = load_database_settings(local(
                        DATABASE_URL=uri, DATABASE_ENVIRONMENT="production",
                        DATABASE_SSLMODE="verify-full", DATABASE_SSLROOTCERT=str(cert)))
                    connection = settings.uri
                    fields = ("drivername", "username", "password", "host", "port", "database")
                    self.assertTrue(tuple(getattr(connection, f) for f in fields) == expected,
                                    "component mismatch")
                    for value in (uri, connection.render_as_string(hide_password=False)):
                        match = grammar.fullmatch(value)
                        self.assertIsNotNone(match, "pinned grammar mismatch")
                        parts = match.groupdict()
                        actual = (parts["drivername"], unquote(parts["username"]),
                                  None if parts["password"] is None else unquote(parts["password"]),
                                  parts["ipv4"] or parts["ipv6"],
                                  int(parts["port"]) if parts["port"] else None, parts["database"])
                        self.assertTrue(actual == expected, "pinned component mismatch")
                        self.assertIsNone(parts["query"])
                    self.assertEqual(str(connection), "DatabaseURI(<redacted>)")
                    self.assertEqual(repr(connection), "DatabaseURI(<redacted>)")
                    if connection.password:
                        self.assertNotIn(connection.password, connection.render_as_string())

    def test_sqlalchemy_runtime_equivalence_when_available(self):
        try:
            import sqlalchemy
            from sqlalchemy.engine import make_url, URL
        except ImportError:
            self.skipTest("SQLAlchemy unavailable; source contract checks only")
        if sqlalchemy.__version__ != "2.0.44":
            self.skipTest("SQLAlchemy 2.0.44 required for pinned runtime comparison")
        for index, (uri, expected) in enumerate(self.accepted_cases()):
            with self.subTest(case=index):
                parsed = make_url(uri)
                fields = ("drivername", "username", "password", "host", "port", "database")
                self.assertTrue(tuple(getattr(parsed, f) for f in fields) == expected,
                                "runtime component mismatch")
                self.assertTrue(parsed == URL.create(**dict(zip(fields, expected))),
                                "URL.create mismatch")
                self.assertFalse(parsed.query)

    def test_bounds(self):
        for key, maximum in (("DATABASE_CONNECT_TIMEOUT", 30), ("DATABASE_POOL_SIZE", 5),
                             ("DATABASE_POOL_TIMEOUT", 30)):
            for value in ("", "0", "-1", "1.5", "nan", "inf", "true", " 2", str(maximum + 1)):
                with self.subTest(key=key, value=value), self.assertRaises(DatabaseConfigurationError):
                    load_database_settings(local(**{key: value}))
            for value in ("1", str(maximum)):
                load_database_settings(local(**{key: value}))

    def test_tls_enforcement(self):
        for mode in ("disable", "allow", "prefer", "require", "verify-ca", ""):
            with self.subTest(mode=mode), self.assertRaises(DatabaseConfigurationError):
                load_database_settings(local(DATABASE_ENVIRONMENT="production", DATABASE_SSLMODE=mode))
        for cert in ("", "relative.pem", str(Path(tempfile.gettempdir()) / "missing-fixture-ca.pem")):
            with self.subTest(cert=cert), self.assertRaises(DatabaseConfigurationError):
                load_database_settings(local(DATABASE_ENVIRONMENT="production",
                                             DATABASE_SSLMODE="verify-full", DATABASE_SSLROOTCERT=cert))
        with tempfile.TemporaryDirectory() as directory:
            cert = Path(directory) / "fixture.pem"
            cert.write_text("synthetic CA placeholder, not a real certificate", encoding="utf-8")
            env = local(DATABASE_ENVIRONMENT="production", DATABASE_SSLMODE="verify-full",
                        DATABASE_SSLROOTCERT=str(cert))
            self.assertEqual(load_database_settings(env).sslmode, "verify-full")
            cert.write_text("", encoding="utf-8")
            with self.assertRaises(DatabaseConfigurationError):
                load_database_settings(env)
        # Secure default applies to development too; plaintext requires explicit opt-in.
        with self.assertRaises(DatabaseConfigurationError):
            load_database_settings({"DATABASE_URL": local()["DATABASE_URL"]})

    def test_redaction(self):
        secret = "synthetic" + "-credential"
        uri = "postgresql+psycopg://fixture:" + secret + "@localhost/fixture"
        settings = load_database_settings(local(DATABASE_URL=uri))
        self.assertNotIn(secret, repr(settings))
        self.assertNotIn(secret, str(settings))
        for overrides in ({"DATABASE_URL": uri + "?password=" + secret},
                          {"DATABASE_POOL_SIZE": secret}, {"DATABASE_ENVIRONMENT": secret},
                          {"DATABASE_SSLMODE": secret},
                          {"DATABASE_SSLMODE": "verify-full", "DATABASE_SSLROOTCERT": secret}):
            with self.assertRaises(DatabaseConfigurationError) as error:
                load_database_settings(local(**overrides))
            self.assertNotIn(secret, str(error.exception))
            self.assertIsNone(error.exception.__cause__)

    def test_inert_import_validation_health_and_lockout(self):
        original_import = builtins.__import__

        def guard(name, *args, **kwargs):
            if name.split(".")[0] in {"sqlalchemy", "psycopg", "alembic"}:
                raise AssertionError("Database dependency imported")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=guard), \
                patch("socket.socket.connect", side_effect=AssertionError("Network access")), \
                patch("socket.create_connection", side_effect=AssertionError("Network access")):
            spec = importlib.util.spec_from_file_location(
                "fixture_database_config", Path(__file__).resolve().parents[1] / "app/database_config.py")
            module = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, {spec.name: module}):
                spec.loader.exec_module(module)
                module.load_database_settings(local())
        # Windows asyncio uses a local socketpair for its own event loop.
        with patch("builtins.__import__", side_effect=guard):
            with application() as (client, services, _, _):
                for environment in ({}, {"DATABASE_ENVIRONMENT": "production", "DATABASE_URL": "invalid"}):
                    with patch.dict("os.environ", environment, clear=True):
                        self.assertEqual(client.get("/health").status_code, 200)
                        self.assertEqual(client.get("/documents").status_code, 401)
                self.assertTrue(all(not service.mock_calls for service in services.values()))


if __name__ == "__main__":
    unittest.main()
