# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Hemeligur
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Tests for configuration via environment variables."""

import os
from unittest.mock import patch

import pytest


class TestDisabledInstancesConfig:
    """Tests for SEARXNG_DISABLED_INSTANCES env var."""

    def test_disabled_instances_parsed_from_env(self):
        """Test parsing disabled instances from env var."""
        from searxng_mcp.constants import get_disabled_instances
        
        with patch.dict(os.environ, {"SEARXNG_DISABLED_INSTANCES": "https://bad1.com, https://bad2.com"}):
            disabled = get_disabled_instances()
            assert "https://bad1.com" in disabled
            assert "https://bad2.com" in disabled
            assert len(disabled) == 2

    def test_disabled_instances_trims_whitespace(self):
        """Test that whitespace is trimmed from URLs."""
        from searxng_mcp.constants import get_disabled_instances
        
        with patch.dict(os.environ, {"SEARXNG_DISABLED_INSTANCES": " https://test.com , https://test2.com "}):
            disabled = get_disabled_instances()
            assert "https://test.com" in disabled
            assert "https://test2.com" in disabled

    def test_disabled_instances_removes_trailing_slash(self):
        """Test that trailing slashes are removed from URLs."""
        from searxng_mcp.constants import get_disabled_instances
        
        with patch.dict(os.environ, {"SEARXNG_DISABLED_INSTANCES": "https://test.com/"}):
            disabled = get_disabled_instances()
            assert "https://test.com" in disabled
            assert "https://test.com/" not in disabled

    def test_disabled_instances_empty_when_not_set(self):
        """Test empty set when env var is not set."""
        from searxng_mcp.constants import get_disabled_instances
        
        env_backup = os.environ.get("SEARXNG_DISABLED_INSTANCES")
        try:
            if "SEARXNG_DISABLED_INSTANCES" in os.environ:
                del os.environ["SEARXNG_DISABLED_INSTANCES"]
            disabled = get_disabled_instances()
            assert disabled == set()
        finally:
            if env_backup is not None:
                os.environ["SEARXNG_DISABLED_INSTANCES"] = env_backup

    def test_disabled_instances_skips_empty_values(self):
        """Test that empty values between commas are skipped."""
        from searxng_mcp.constants import get_disabled_instances
        
        with patch.dict(os.environ, {"SEARXNG_DISABLED_INSTANCES": "https://test.com,,https://test2.com"}):
            disabled = get_disabled_instances()
            assert "https://test.com" in disabled
            assert "https://test2.com" in disabled
            assert "" not in disabled


class TestDebugToolsConfig:
    """Tests for SEARXNG_DEBUG_TOOLS env var."""

    def test_debug_tools_true(self):
        """Test debug tools enabled when env var is 'true'."""
        from searxng_mcp.constants import is_debug_enabled
        
        with patch.dict(os.environ, {"SEARXNG_DEBUG_TOOLS": "true"}):
            assert is_debug_enabled() is True

    def test_debug_tools_false_lowercase(self):
        """Test debug tools disabled when env var is 'false'."""
        from searxng_mcp.constants import is_debug_enabled
        
        with patch.dict(os.environ, {"SEARXNG_DEBUG_TOOLS": "false"}):
            assert is_debug_enabled() is False

    def test_debug_tools_1(self):
        """Test debug tools enabled when env var is '1'."""
        from searxng_mcp.constants import is_debug_enabled
        
        with patch.dict(os.environ, {"SEARXNG_DEBUG_TOOLS": "1"}):
            assert is_debug_enabled() is True

    def test_debug_tools_0(self):
        """Test debug tools disabled when env var is '0'."""
        from searxng_mcp.constants import is_debug_enabled
        
        with patch.dict(os.environ, {"SEARXNG_DEBUG_TOOLS": "0"}):
            assert is_debug_enabled() is False

    def test_debug_tools_empty(self):
        """Test debug tools disabled when env var is empty."""
        from searxng_mcp.constants import is_debug_enabled
        
        with patch.dict(os.environ, {"SEARXNG_DEBUG_TOOLS": ""}):
            assert is_debug_enabled() is False

    def test_debug_tools_not_set(self):
        """Test debug tools disabled when env var is not set."""
        from searxng_mcp.constants import is_debug_enabled
        
        env_backup = os.environ.get("SEARXNG_DEBUG_TOOLS")
        try:
            if "SEARXNG_DEBUG_TOOLS" in os.environ:
                del os.environ["SEARXNG_DEBUG_TOOLS"]
            assert is_debug_enabled() is False
        finally:
            if env_backup is not None:
                os.environ["SEARXNG_DEBUG_TOOLS"] = env_backup


class TestBackoffConfig:
    """Tests for SEARXNG_BACKOFF_BASE and SEARXNG_BACKOFF_MAX env vars."""

    def test_backoff_base_from_env(self):
        """Test backoff base value from env var."""
        from searxng_mcp.constants import get_backoff_base
        
        with patch.dict(os.environ, {"SEARXNG_BACKOFF_BASE": "120"}):
            assert get_backoff_base() == 120

    def test_backoff_base_default(self):
        """Test backoff base default value."""
        from searxng_mcp.constants import get_backoff_base
        
        env_backup = os.environ.get("SEARXNG_BACKOFF_BASE")
        try:
            if "SEARXNG_BACKOFF_BASE" in os.environ:
                del os.environ["SEARXNG_BACKOFF_BASE"]
            assert get_backoff_base() == 60
        finally:
            if env_backup is not None:
                os.environ["SEARXNG_BACKOFF_BASE"] = env_backup

    def test_backoff_max_from_env(self):
        """Test backoff max value from env var."""
        from searxng_mcp.constants import get_backoff_max
        
        with patch.dict(os.environ, {"SEARXNG_BACKOFF_MAX": "1800"}):
            assert get_backoff_max() == 1800

    def test_backoff_max_default(self):
        """Test backoff max default value."""
        from searxng_mcp.constants import get_backoff_max
        
        env_backup = os.environ.get("SEARXNG_BACKOFF_MAX")
        try:
            if "SEARXNG_BACKOFF_MAX" in os.environ:
                del os.environ["SEARXNG_BACKOFF_MAX"]
            assert get_backoff_max() == 900
        finally:
            if env_backup is not None:
                os.environ["SEARXNG_BACKOFF_MAX"] = env_backup


class TestInstanceDisabledField:
    """Tests for InstanceStatus.disabled field."""

    def test_disabled_instance_not_available(self):
        """Test that disabled instances return False from is_available()."""
        from searxng_mcp.models import InstanceStatus
        
        status = InstanceStatus(url="https://test.com")
        status.disabled = True
        assert status.is_available() is False

    def test_enabled_instance_available(self):
        """Test that enabled instances return True from is_available()."""
        from searxng_mcp.models import InstanceStatus
        
        status = InstanceStatus(url="https://test.com")
        status.disabled = False
        assert status.is_available() is True

    def test_disabled_to_dict(self):
        """Test that disabled field is included in to_dict()."""
        from searxng_mcp.models import InstanceStatus
        
        status = InstanceStatus(url="https://test.com")
        status.disabled = True
        data = status.to_dict()
        assert data["disabled"] is True
        
        status.disabled = False
        data = status.to_dict()
        assert data["disabled"] is False


class TestManagerDisabledInstances:
    """Tests for manager handling of disabled instances."""

    @pytest.mark.asyncio
    async def test_manager_applies_disabled_instances(self):
        """Test that manager marks instances as disabled on init."""
        from searxng_mcp.manager import SearXNGManager
        
        with patch.dict(os.environ, {"SEARXNG_DISABLED_INSTANCES": "https://fallback1.com"}):
            manager = SearXNGManager()
            # Add an instance that should be disabled
            manager.instances["https://fallback1.com"] = __import__("searxng_mcp.models", fromlist=["InstanceStatus"]).InstanceStatus(url="https://fallback1.com")
            
            # Re-apply disabled instances
            manager._apply_disabled_instances()
            
            assert manager.instances["https://fallback1.com"].disabled is True
            assert manager.instances["https://fallback1.com"].is_available() is False
