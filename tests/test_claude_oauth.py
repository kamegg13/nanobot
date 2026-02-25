"""Tests for Claude OAuth token authentication flow."""

import os
from unittest.mock import MagicMock, patch

import pytest

from nanobot.config.schema import Config, ProviderConfig, ProvidersConfig
from nanobot.providers.litellm_provider import LiteLLMProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config_with_anthropic(**kwargs) -> Config:
    """Build a minimal Config with an Anthropic provider config."""
    provider = ProviderConfig(**kwargs)
    providers = ProvidersConfig(anthropic=provider)
    return Config(providers=providers)


# ---------------------------------------------------------------------------
# schema.py: ProviderConfig.oauth_token field
# ---------------------------------------------------------------------------

class TestProviderConfigOauthToken:
    def test_default_is_empty_string(self):
        p = ProviderConfig()
        assert p.oauth_token == ""

    def test_set_via_constructor(self):
        p = ProviderConfig(oauth_token="sk-ant-oaut01-test")
        assert p.oauth_token == "sk-ant-oaut01-test"

    def test_camel_case_alias(self):
        """Pydantic accepts camelCase alias oauthToken (from JSON config)."""
        p = ProviderConfig.model_validate({"oauthToken": "mytoken"})
        assert p.oauth_token == "mytoken"


# ---------------------------------------------------------------------------
# schema.py: _match_provider accepts oauth_token
# ---------------------------------------------------------------------------

class TestMatchProviderWithOauthToken:
    def test_matches_anthropic_via_oauth_token_no_api_key(self):
        config = _config_with_anthropic(oauth_token="sk-ant-oaut01-test")
        p, name = config._match_provider("claude-3-5-sonnet")
        assert name == "anthropic"
        assert p is not None

    def test_matches_anthropic_via_api_key_still_works(self):
        config = _config_with_anthropic(api_key="sk-ant-api03-real")
        p, name = config._match_provider("claude-3-5-sonnet")
        assert name == "anthropic"

    def test_no_credentials_returns_none(self):
        config = _config_with_anthropic()
        p, name = config._match_provider("claude-3-5-sonnet")
        assert name is None


# ---------------------------------------------------------------------------
# commands.py: _make_provider — env var resolution
# ---------------------------------------------------------------------------

class TestMakeProviderOauthResolution:
    def _call_make_provider(self, config: Config, env: dict):
        """Call _make_provider with mocked env and LiteLLMProvider."""
        from nanobot.cli.commands import _make_provider

        created = {}

        def fake_litellm(**kwargs):
            created.update(kwargs)
            provider = MagicMock(spec=LiteLLMProvider)
            provider._created_with = kwargs
            return provider

        # LiteLLMProvider is lazy-imported inside _make_provider, so patch the source module
        with patch.dict(os.environ, env, clear=False), \
             patch("nanobot.providers.litellm_provider.LiteLLMProvider", fake_litellm):
            result = _make_provider(config)

        return result, created

    def test_env_var_injects_bearer_header(self):
        config = _config_with_anthropic()  # no api_key, no oauth_token in config
        _, kwargs = self._call_make_provider(
            config, {"CLAUDE_OAUTH_TOKEN": "sk-ant-oaut01-envtoken"}
        )
        assert kwargs["extra_headers"]["Authorization"] == "Bearer sk-ant-oaut01-envtoken"
        assert kwargs["api_key"] == "claude-oauth"

    def test_config_file_oauth_token_used_when_no_env_var(self):
        config = _config_with_anthropic(oauth_token="sk-ant-oaut01-configtoken")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_OAUTH_TOKEN"}
        with patch.dict(os.environ, env, clear=True):
            _, kwargs = self._call_make_provider(config, {})
        assert kwargs["extra_headers"]["Authorization"] == "Bearer sk-ant-oaut01-configtoken"

    def test_env_var_takes_priority_over_config_file(self):
        config = _config_with_anthropic(oauth_token="config-token")
        _, kwargs = self._call_make_provider(
            config, {"CLAUDE_OAUTH_TOKEN": "env-token"}
        )
        assert kwargs["extra_headers"]["Authorization"] == "Bearer env-token"

    def test_oauth_takes_priority_over_api_key(self):
        """When both oauth_token and api_key are set, oauth wins."""
        config = _config_with_anthropic(api_key="sk-ant-api03-real", oauth_token="sk-ant-oaut01-token")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_OAUTH_TOKEN"}
        with patch.dict(os.environ, env, clear=True):
            _, kwargs = self._call_make_provider(config, {})
        assert "Authorization" in kwargs["extra_headers"]
        assert kwargs["extra_headers"]["Authorization"].startswith("Bearer ")

    def test_existing_extra_headers_preserved(self):
        config = _config_with_anthropic(
            oauth_token="mytoken",
            extra_headers={"X-Custom": "value"},
        )
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_OAUTH_TOKEN"}
        with patch.dict(os.environ, env, clear=True):
            _, kwargs = self._call_make_provider(config, {})
        assert kwargs["extra_headers"]["X-Custom"] == "value"
        assert kwargs["extra_headers"]["Authorization"] == "Bearer mytoken"


# ---------------------------------------------------------------------------
# litellm_provider.py: OAuth error message
# ---------------------------------------------------------------------------

class TestOauthErrorMessage:
    def _provider_with_bearer(self) -> LiteLLMProvider:
        p = LiteLLMProvider.__new__(LiteLLMProvider)
        p.extra_headers = {"Authorization": "Bearer sk-ant-oaut01-test"}
        p.api_key = "claude-oauth"
        p.api_base = None
        p.default_model = "claude-3-5-sonnet"
        p._gateway = None
        return p

    @pytest.mark.asyncio
    async def test_401_returns_oauth_specific_message(self):
        provider = self._provider_with_bearer()
        with patch("nanobot.providers.litellm_provider.acompletion", side_effect=Exception("401 Unauthorized")):
            response = await provider.chat(messages=[{"role": "user", "content": "hi"}])
        assert "OAuth token" in response.content
        assert "expired" in response.content

    @pytest.mark.asyncio
    async def test_non_auth_error_keeps_generic_message(self):
        provider = self._provider_with_bearer()
        with patch("nanobot.providers.litellm_provider.acompletion", side_effect=Exception("500 Internal Server Error")):
            response = await provider.chat(messages=[{"role": "user", "content": "hi"}])
        assert "Error calling LLM" in response.content
        assert "OAuth token" not in response.content
