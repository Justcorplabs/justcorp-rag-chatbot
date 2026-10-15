"""Exercise real route registration with isolated imports and mocked providers."""
import builtins
from contextlib import contextmanager
import importlib
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
FLAGS = ("ENABLE_WHATSAPP_ROUTES", "ENABLE_TEST_ANSWER_ROUTE")
NORMAL = {
    "/": "get", "/health": "get", "/upload-document": "post",
    "/documents": "get", "/documents/{document_id}": "delete",
    "/search": "post", "/ask": "post",
}
OPTIONAL = (("get", "/whatsapp/webhook"),
            ("post", "/whatsapp/webhook"),
            ("post", "/whatsapp/send-test"), ("post", "/test-answer"))


@contextmanager
def application(whatsapp=None, answer=None):
    # Never read local .env files or instantiate real service singletons.
    saved = {k: v for k, v in sys.modules.items() if k == "app" or k.startswith("app.")}
    for name in saved:
        del sys.modules[name]
    services = {}
    modules = {}
    for name, attributes in {
        "document_loader": ("extract_text_from_pdf", "clean_extracted_text"),
        "chunker": ("split_text_into_chunks",),
        "embeddings": ("embedding_model",),
        "vector_store": ("vector_store",),
        "rag_pipeline": ("rag_pipeline",),
        "llm_client": ("llm_client",),
        "whatsapp_client": ("whatsapp_client",),
        "chatbot_service": ("get_chatbot_answer",),
    }.items():
        module = ModuleType("app." + name)
        for attribute in attributes:
            services[attribute] = Mock(name=attribute)
            setattr(module, attribute, services[attribute])
        modules[module.__name__] = module
    imports = []
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name in {"app.whatsapp_webhook", "app.whatsapp_client", "app.chatbot_service"}:
            imports.append(name)
            if whatsapp is None or whatsapp.strip().lower() != "true":
                raise AssertionError("Disabled WhatsApp module imported")
        return original_import(name, *args, **kwargs)

    try:
        with tempfile.TemporaryDirectory() as directory:
            environment = {"UPLOAD_DIR": str(Path(directory) / "uploads"),
                           "CHROMA_DB_PATH": str(Path(directory) / "chroma")}
            for flag, value in zip(FLAGS, (whatsapp, answer)):
                if value is not None:
                    environment[flag] = value
            with patch.dict(os.environ, environment, clear=True), \
                    patch("dotenv.load_dotenv"), patch.dict(sys.modules, modules), \
                    patch("builtins.__import__", side_effect=guarded_import):
                main = importlib.import_module("app.main")
                with TestClient(main.app) as client:
                    yield client, services, imports, main
    finally:
        for name in list(sys.modules):
            if name == "app" or name.startswith("app."):
                del sys.modules[name]
        sys.modules.update(saved)


class OptionalRoutesTests(unittest.TestCase):
    def check_registration(self, whatsapp=None, answer=None):
        with application(whatsapp, answer) as (client, services, imports, main):
            enabled = (main.settings.ENABLE_WHATSAPP_ROUTES,
                       main.settings.ENABLE_TEST_ANSWER_ROUTE)
            schema = client.get("/openapi.json").json()
            paths = schema["paths"]
            for path, method in NORMAL.items():
                self.assertIn(method, paths[path])
            self.assertEqual(client.get("/health").status_code, 200)
            for index, (method, path) in enumerate(OPTIONAL):
                active = enabled[0 if index < 3 else 1]
                self.assertEqual(method in paths.get(path, {}), active)
                if not active:
                    self.assertNotIn(path, paths)
                    for body in ({}, {"question": "hello", "to": "test", "message": "hello"}):
                        response = client.request(method, path, json=body)
                        self.assertEqual(response.status_code, 404)
            for service in services.values():
                self.assertEqual(service.mock_calls, [])
            if not enabled[0]:
                self.assertEqual(imports, [])
                self.assertNotIn("app.whatsapp_webhook", sys.modules)
            if not enabled[1]:
                self.assertNotIn("TestAnswerRequest", schema.get("components", {}).get("schemas", {}))
                self.assertNotIn("TestAnswerResponse", schema.get("components", {}).get("schemas", {}))

    def test_defaults_without_credentials_or_whatsapp_imports(self):
        self.check_registration()

    def test_all_flag_combinations(self):
        for whatsapp in ("false", "true"):
            for answer in ("false", "true"):
                with self.subTest(whatsapp=whatsapp, answer=answer):
                    self.check_registration(whatsapp, answer)

    def test_invalid_values_fail_closed_independently(self):
        for value in ("", "false", "FALSE", "0", "1", "yes", "on", "unknown", "tru", " true false "):
            for values in ((value, "true"), ("true", value)):
                with self.subTest(values=values):
                    self.check_registration(*values)

    def test_explicit_true_normalization(self):
        self.check_registration(" TRUE ", "True")

    def test_enabled_handlers_with_mocked_providers(self):
        with application("true", "true") as (client, services, _, main):
            chunk = dict(document_id="fixture", filename="fixture.pdf", chunk_number=1,
                         distance=0.1, text="Fixture context")
            services["rag_pipeline"].retrieve_context.return_value = [chunk]
            services["llm_client"].generate_answer.return_value = "Fixture answer"
            response = client.post("/test-answer", json={"question": " hello ", "top_k": 2})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["answer"], "Fixture answer")
            services["rag_pipeline"].retrieve_context.assert_called_once_with(question="hello", top_k=2)
            services["llm_client"].generate_answer.assert_called_once_with(question="hello", retrieved_chunks=[chunk])
            self.assertEqual(client.post("/test-answer", json={"question": " "}).status_code, 400)
            services["rag_pipeline"].retrieve_context.return_value = []
            self.assertEqual(client.post("/test-answer", json={"question": "missing"}).status_code, 404)
            response = client.get("/whatsapp/webhook", params={
                "hub.mode": "subscribe", "hub.verify_token": main.settings.WHATSAPP_VERIFY_TOKEN,
                "hub.challenge": "123"})
            self.assertEqual(response.json(), 123)
            self.assertEqual(client.get("/whatsapp/webhook").status_code, 403)
            services["whatsapp_client"].send_text_message.return_value = {"messages": []}
            self.assertEqual(client.post("/whatsapp/send-test", json={"to": "fixture", "message": "hello"}).status_code, 200)
            services["whatsapp_client"].send_text_message.assert_called_once_with(to_phone_number="fixture", message_text="hello")
            services["get_chatbot_answer"].return_value = {"answer": "Fixture answer", "sources": []}
            payload = {"entry": [{"changes": [{"value": {"messages": [
                {"type": "text", "from": "fixture", "text": {"body": "hello"}}
            ]}}]}]}
            response = client.post("/whatsapp/webhook", json=payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["replies_sent"][0]["status"], "sent")
            services["get_chatbot_answer"].assert_called_once_with(question="hello", top_k=4)
            self.assertEqual(services["whatsapp_client"].send_text_message.call_count, 2)


if __name__ == "__main__":
    unittest.main()
