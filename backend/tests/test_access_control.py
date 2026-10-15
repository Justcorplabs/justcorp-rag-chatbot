"""SEC03 boundary tests: synthetic principals and providers only."""
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
import builtins
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_optional_routes import application


class AccessControlTests(unittest.TestCase):
    @contextmanager
    def storage_isolated_application(self):
        # The store defaults to a path relative to cwd, not CHROMA_DB_PATH.
        # Change cwd before application import so startup writes are isolated too.
        previous_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                with application("true", "true") as context:
                    main = context[3]
                    storage_dir = Path(getattr(
                        main.settings, "VECTOR_STORE_DIR", "vector_store_data"
                    )).resolve()
                    self.assertTrue(storage_dir.is_relative_to(Path(directory).resolve()))
                    self.assertFalse(storage_dir.exists(), "Storage created during startup")
                    yield (*context, storage_dir)
            finally:
                os.chdir(previous_directory)

    def test_policy_validator_rejects_unknown_and_unguarded_routes(self):
        with application() as (_, _, _, main):
            route = next(r for r in main.app.routes if r.path == "/documents")
            dependencies = route.dependant.dependencies
            try:
                route.dependant.dependencies = []
                with self.assertRaises(RuntimeError):
                    main.validate_route_policy()
            finally:
                route.dependant.dependencies = dependencies
            main.app.get("/unclassified")(lambda: {})
            with self.assertRaises(RuntimeError):
                main.validate_route_policy()

    def test_startup_and_health_never_import_providers(self):
        original = builtins.__import__
        blocked = {"app." + name for name in (
            "llm_client", "rag_pipeline", "vector_store", "embeddings",
            "document_loader", "chunker", "whatsapp_client", "chatbot_service")}

        def guard(name, *args, **kwargs):
            if name in blocked:
                raise AssertionError("Provider imported during startup or denial")
            return original(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=guard):
            with self.storage_isolated_application() as (client, _, _, main, storage_dir):
                for path in ("/", "/health"):
                    self.assertEqual(client.get(path).status_code, 200)
                    self.assertFalse(storage_dir.exists(), "Storage created by public health")
                for (method, path), dependency in main.ROUTE_POLICY.items():
                    if dependency is not None:
                        self.assertEqual(self.request(client, method, path).status_code, 401)
                        self.assertFalse(storage_dir.exists(), "Storage created by denied request")

    def request(self, client, method, path, **kwargs):
        if path == "/upload-document":
            return client.request(method, path, files={"file": ("fixture.pdf", b"synthetic", "application/pdf")}, **kwargs)
        return client.request(method, path.replace("{document_id}", "fixture"),
                              json={"question": "fixture", "to": "fixture", "message": "hello"}, **kwargs)

    def test_denials_inventory_and_no_service_imports(self):
        with self.storage_isolated_application() as (client, services, _, main, storage_dir):
            from app.auth import require_admin, require_user
            original = builtins.__import__
            blocked = {"app." + name for name in (
                "llm_client", "rag_pipeline", "vector_store", "embeddings",
                "document_loader", "chunker", "whatsapp_client", "chatbot_service")}

            def guard(name, *args, **kwargs):
                if name in blocked:
                    raise AssertionError("Protected service imported before authorization")
                return original(name, *args, **kwargs)

            expected = set(main.ROUTE_POLICY)
            actual = {(method, route.path) for route in main.app.routes for method in route.methods}
            self.assertEqual(actual, expected)
            with patch("builtins.__import__", side_effect=guard):
                for (method, path), dependency in main.ROUTE_POLICY.items():
                    route = next(r for r in main.app.routes if r.path == path and method in r.methods)
                    if dependency is None:
                        self.assertEqual(client.request(method, path).json(), {"status": "ok"})
                        self.assertFalse(storage_dir.exists(), "Storage created by public health")
                        continue
                    self.assertIn(dependency, (require_user, require_admin))
                    self.assertIn(dependency, [d.call for d in route.dependant.dependencies])
                    for headers in ({}, {"Authorization": "Bearer fabricated", "Cookie": "session=fabricated",
                                         "X-Role": "admin", "X-User-Id": "fixture"}):
                        self.assertEqual(self.request(client, method, path, headers=headers,
                                                      params={"role": "admin", "user_id": "fixture"}).status_code, 401)
                        self.assertFalse(storage_dir.exists(), "Storage created by denied request")
                for path in ("/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"):
                    self.assertEqual(client.get(path).status_code, 404)
            self.assertFalse(Path(main.settings.UPLOAD_DIR).exists())
            self.assertFalse(storage_dir.exists())
            for service in services.values():
                self.assertEqual(service.mock_calls, [])

    def test_identity_validation_and_cleanup(self):
        with application("true", "true") as (client, services, _, main):
            from app.auth import Principal, resolve_verified_principal
            for values in (("", True, "member"), (" ", True, "admin"),
                           (1, True, "member"), ("fixture", 1, "admin"),
                           ("fixture", True, "owner")):
                with self.assertRaises(ValueError):
                    Principal(*values)
            principal = Principal("fixture", True, "member")
            with self.assertRaises(FrozenInstanceError):
                principal.role = "admin"
            malformed = object.__new__(Principal)
            for identity, status in ((None, 401), ({"role": "admin"}, 401),
                                     (malformed, 401), (Principal("fixture", False, "admin"), 403)):
                main.app.dependency_overrides[resolve_verified_principal] = lambda: identity
                try:
                    for (method, path), guard in main.ROUTE_POLICY.items():
                        if guard is not None:
                            self.assertEqual(self.request(client, method, path).status_code, status)
                finally:
                    main.app.dependency_overrides.clear()
            self.assertEqual(client.get("/documents").status_code, 401)
            self.assertEqual(main.app.dependency_overrides, {})
            for service in services.values():
                self.assertEqual(service.mock_calls, [])

    def test_member_and_admin_handlers(self):
        with application("true", "true") as (client, services, _, main):
            from app.auth import Principal, require_admin, resolve_verified_principal
            chunk = dict(document_id="fixture", filename="fixture.pdf", chunk_number=1,
                         distance=0.1, text="Synthetic context")
            services["vector_store"].list_documents.return_value = []
            services["vector_store"].delete_document.return_value = 1
            services["rag_pipeline"].retrieve_context.return_value = [chunk]
            services["llm_client"].generate_answer.return_value = "Synthetic answer"
            services["extract_text_from_pdf"].return_value = "Synthetic text"
            services["clean_extracted_text"].return_value = "Synthetic text"
            services["split_text_into_chunks"].return_value = [chunk]
            services["embedding_model"].embed_texts.return_value = [[0.1, 0.2]]
            services["vector_store"].add_document_chunks.return_value = 1
            for role in ("member", "admin"):
                main.app.dependency_overrides[resolve_verified_principal] = lambda: Principal("fixture", True, role)
                try:
                    for (method, path), guard in main.ROUTE_POLICY.items():
                        if role == "member" and path.startswith("/whatsapp"):
                            self.assertEqual(self.request(client, method, path).status_code, 403)
                        if guard is None or path.startswith("/whatsapp"):
                            continue
                        status = 403 if role == "member" and guard is require_admin else 200
                        self.assertEqual(self.request(client, method, path).status_code, status)
                finally:
                    main.app.dependency_overrides.clear()
            services["vector_store"].list_documents.assert_called_with()
            services["vector_store"].delete_document.assert_called_once_with(document_id="fixture")
            services["extract_text_from_pdf"].assert_called_once()
            services["embedding_model"].embed_texts.assert_called_once()
            self.assertEqual(services["rag_pipeline"].retrieve_context.call_count, 5)
            self.assertEqual(services["llm_client"].generate_answer.call_count, 3)
            self.assertEqual(client.get("/documents").status_code, 401)


if __name__ == "__main__":
    unittest.main()
