import os
import unittest
from unittest.mock import patch

from app.config import Settings


class SettingsConfigurationTests(unittest.TestCase):
    def test_gemini_api_key_environment_variable(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"}, clear=False):
            settings = Settings(_env_file=None)
        self.assertEqual(settings.active_api_key, "test-key")
        self.assertTrue(settings.ai_configured)

    def test_google_api_key_is_accepted_as_a_fallback(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "gemini", "GOOGLE_API_KEY": "google-test-key"}, clear=False):
            with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
                settings = Settings(_env_file=None)
        self.assertEqual(settings.active_api_key, "google-test-key")

    def test_legacy_flash_lite_model_is_migrated(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "gemini", "OPENAI_MODEL": "gemini-2.5-flash-lite"}, clear=False):
            settings = Settings(_env_file=None)
        self.assertTrue(settings.model_migrated)
        self.assertEqual(settings.model_name, "gemini-3.8-flash")

    def test_provider_name_is_normalized(self):
        with patch.dict(os.environ, {"AI_PROVIDER": " Gemini "}, clear=False):
            settings = Settings(_env_file=None)
        self.assertEqual(settings.normalized_ai_provider, "gemini")


if __name__ == "__main__":
    unittest.main()
