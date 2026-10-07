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

"""Persistent state management for SearXNG instances.

Manages saving and loading instance state (circuit breaker, backoff)
to/from disk for persistence across server restarts.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from .models import CircuitState, InstanceStatus

logger = logging.getLogger(__name__)

# Cache directory and state file
CACHE_DIR = Path.home() / ".cache" / "searxng-mcp"
STATE_FILE = CACHE_DIR / "instance_state.json"


def _ensure_cache_dir() -> None:
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_instance_states() -> dict[str, InstanceStatus]:
    """Load instance states from disk.
    
    Returns:
        Dictionary mapping URL to InstanceStatus.
    """
    if not STATE_FILE.exists():
        logger.debug("No instance state file found")
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        instances: dict[str, InstanceStatus] = {}
        for url, state_data in data.get("instances", {}).items():
            status = InstanceStatus(url=url)
            status.state = CircuitState(state_data.get("state", "closed"))
            status.failure_count = state_data.get("failure_count", 0)
            status.last_failure = state_data.get("last_failure")
            status.last_success = state_data.get("last_success")
            status.circuit_open_at = state_data.get("circuit_open_at")
            status.error_message = state_data.get("error_message")
            status.backoff_until = state_data.get("backoff_until")
            instances[url] = status

        logger.info(f"Loaded state for {len(instances)} instances from disk")
        return instances

    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load instance state: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading instance state: {e}")
        return {}


def save_instance_states(instances: dict[str, InstanceStatus]) -> bool:
    """Save instance states to disk.
    
    Args:
        instances: Dictionary mapping URL to InstanceStatus.
        
    Returns:
        True if saved successfully, False otherwise.
    """
    _ensure_cache_dir()

    data = {
        "version": 1,
        "saved_at": __import__("time").time(),
        "instances": {
            url: {
                "state": status.state.value,
                "failure_count": status.failure_count,
                "last_failure": status.last_failure,
                "last_success": status.last_success,
                "circuit_open_at": status.circuit_open_at,
                "error_message": status.error_message,
                "backoff_until": status.backoff_until,
            }
            for url, status in instances.items()
        },
    }

    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved state for {len(instances)} instances to disk")
        return True
    except IOError as e:
        logger.error(f"Failed to save instance state: {e}")
        return False


def clear_instance_states() -> bool:
    """Clear all persisted instance states.
    
    Returns:
        True if cleared successfully, False otherwise.
    """
    if STATE_FILE.exists():
        try:
            STATE_FILE.unlink()
            logger.info("Instance state file cleared")
            return True
        except IOError as e:
            logger.error(f"Failed to clear instance state: {e}")
            return False
    return True


def get_state_info() -> Optional[dict]:
    """Get information about the state file.
    
    Returns:
        Dictionary with state info or None if no state file exists.
    """
    if not STATE_FILE.exists():
        return None

    try:
        stat = STATE_FILE.stat()
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return {
            "file": str(STATE_FILE),
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
            "instance_count": len(data.get("instances", {})),
            "saved_at": data.get("saved_at"),
        }
    except (json.JSONDecodeError, IOError):
        return None
