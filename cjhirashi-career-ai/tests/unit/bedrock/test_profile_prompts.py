"""Unit tests for per-agent profile prompt overrides."""
import pytest

from services.agent_profiles import get_profile, list_profiles


def test_all_profiles_have_default_suffix():
    for profile in list_profiles():
        assert profile.system_prompt_suffix.strip()
        assert get_profile(profile.id).id == profile.id


def test_unknown_profile_raises():
    with pytest.raises(KeyError):
        get_profile("nonexistent_profile")
