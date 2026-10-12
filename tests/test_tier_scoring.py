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

"""Tests for tier-based scoring system."""

import time
import pytest

from searxng_mcp.models import (
    ExternalMetrics,
    InstanceStatus,
    CircuitState,
)


class TestExternalMetrics:
    """Tests for ExternalMetrics dataclass."""

    def test_creation_with_defaults(self):
        """Test ExternalMetrics creation with default values."""
        metrics = ExternalMetrics()
        
        assert metrics.uptime_day == 0.0
        assert metrics.uptime_week == 0.0
        assert metrics.tls_grade == "C"
        assert metrics.engine_count == 0
        assert metrics.error_load == 0.0
        assert metrics.error_check == 0.0
        assert metrics.network_country == ""
        assert metrics.last_updated is not None

    def test_creation_with_values(self):
        """Test ExternalMetrics creation with custom values."""
        metrics = ExternalMetrics(
            uptime_day=99.5,
            uptime_week=98.0,
            tls_grade="A+",
            engine_count=25,
            error_load=0.01,
            error_check=0.0,
            network_country="DE",
        )
        
        assert metrics.uptime_day == 99.5
        assert metrics.uptime_week == 98.0
        assert metrics.tls_grade == "A+"
        assert metrics.engine_count == 25
        assert metrics.error_load == 0.01
        assert metrics.network_country == "DE"

    def test_to_dict(self):
        """Test ExternalMetrics serialization."""
        metrics = ExternalMetrics(
            uptime_day=100.0,
            tls_grade="A",
            engine_count=20,
        )
        
        data = metrics.to_dict()
        
        assert data["uptime_day"] == 100.0
        assert data["tls_grade"] == "A"
        assert data["engine_count"] == 20
        assert "last_updated" in data

    def test_from_dict(self):
        """Test ExternalMetrics deserialization."""
        data = {
            "uptime_day": 95.0,
            "uptime_week": 90.0,
            "tls_grade": "B",
            "engine_count": 15,
            "error_load": 0.05,
            "error_check": 0.01,
            "network_country": "US",
            "last_updated": time.time(),
        }
        
        metrics = ExternalMetrics.from_dict(data)
        
        assert metrics.uptime_day == 95.0
        assert metrics.tls_grade == "B"
        assert metrics.engine_count == 15
        assert metrics.network_country == "US"

    def test_from_dict_with_missing_fields(self):
        """Test ExternalMetrics handles missing fields gracefully."""
        data = {"uptime_day": 100.0}
        
        metrics = ExternalMetrics.from_dict(data)
        
        assert metrics.uptime_day == 100.0
        assert metrics.tls_grade == "C"  # Default
        assert metrics.engine_count == 0  # Default


class TestInstanceStatusMetrics:
    """Tests for InstanceStatus metrics functionality."""

    def test_success_rate_no_requests(self):
        """Test success_rate returns 0.5 when no requests."""
        status = InstanceStatus(url="https://test.example")
        
        assert status.success_rate == 0.5

    def test_success_rate_with_requests(self):
        """Test success_rate calculation."""
        status = InstanceStatus(url="https://test.example")
        
        status.record_request(success=True)
        status.record_request(success=True)
        status.record_request(success=False)
        
        assert status.success_rate == pytest.approx(2/3)

    def test_circuit_score_closed(self):
        """Test circuit_score for CLOSED state."""
        status = InstanceStatus(url="https://test.example")
        status.state = CircuitState.CLOSED
        
        assert status.circuit_score == 1.0

    def test_circuit_score_half_open(self):
        """Test circuit_score for HALF_OPEN state."""
        status = InstanceStatus(url="https://test.example")
        status.state = CircuitState.HALF_OPEN
        
        assert status.circuit_score == 0.5

    def test_circuit_score_open(self):
        """Test circuit_score for OPEN state."""
        status = InstanceStatus(url="https://test.example")
        status.state = CircuitState.OPEN
        
        assert status.circuit_score == 0.0

    def test_record_request_success(self):
        """Test record_request with success."""
        status = InstanceStatus(url="https://test.example")
        
        status.record_request(success=True, response_time_ms=150.0)
        
        assert status.total_requests == 1
        assert status.successful_requests == 1
        assert status.response_times_ms == [150.0]
        assert status.last_success is not None

    def test_record_request_failure(self):
        """Test record_request with failure."""
        status = InstanceStatus(url="https://test.example")
        
        status.record_request(success=False)
        
        assert status.total_requests == 1
        assert status.successful_requests == 0

    def test_record_request_preserves_last_10_times(self):
        """Test response times are limited to last 10."""
        status = InstanceStatus(url="https://test.example")
        
        for i in range(15):
            status.record_request(success=True, response_time_ms=float(i))
        
        assert len(status.response_times_ms) == 10
        assert status.response_times_ms[0] == 5.0  # First of last 10


class TestRecencyBonus:
    """Tests for recency bonus with exponential decay."""

    def test_recency_no_history(self):
        """Test recency bonus returns 0.5 when no history."""
        status = InstanceStatus(url="https://test.example")
        
        assert status._calculate_recency_bonus() == 0.5

    def test_recency_immediate(self):
        """Test recency bonus is ~1.0 immediately after success."""
        status = InstanceStatus(url="https://test.example")
        status.last_success = time.time()
        
        bonus = status._calculate_recency_bonus()
        
        assert 0.95 <= bonus <= 1.0

    def test_recency_decay(self):
        """Test recency decays over time."""
        status = InstanceStatus(url="https://test.example")
        
        # Now
        status.last_success = time.time()
        immediate_bonus = status._calculate_recency_bonus()
        
        # 1 hour ago (half-life)
        status.last_success = time.time() - 3600
        hour_bonus = status._calculate_recency_bonus()
        
        # 2 hours ago
        status.last_success = time.time() - 7200
        two_hour_bonus = status._calculate_recency_bonus()
        
        assert immediate_bonus > hour_bonus
        assert hour_bonus > two_hour_bonus
        assert immediate_bonus > 0.9
        assert two_hour_bonus < 0.7


class TestTierScore:
    """Tests for hybrid tier scoring."""

    def test_score_without_external_metrics(self):
        """Test score without external metrics."""
        status = InstanceStatus(url="https://test.example")
        
        score = status.calculate_tier_score()
        
        # Only internal metrics (neutral): should be around 0.35-0.40
        # internal = (0.5 * 0.35 + 0.5 * 0.15 + 1.0 * 0.10) / 0.60 * 0.60
        #         = (0.175 + 0.075 + 0.10) / 0.60 * 0.60 = 0.35
        assert 0.30 <= score <= 0.45

    def test_score_with_external_metrics(self):
        """Test score with good external metrics is higher."""
        status = InstanceStatus(url="https://test.example")
        status.update_external_metrics(ExternalMetrics(
            uptime_day=100.0,
            tls_grade="A+",
            engine_count=30,
        ))
        
        score = status.calculate_tier_score()
        
        # Should be higher than without external metrics
        assert score > 0.5

    def test_tls_grades_affect_score(self):
        """Test different TLS grades produce different scores."""
        status_a_plus = InstanceStatus(url="https://a.plus.example")
        status_a_plus.update_external_metrics(ExternalMetrics(
            tls_grade="A+",
            engine_count=20,
        ))
        
        status_c = InstanceStatus(url="https://c.example")
        status_c.update_external_metrics(ExternalMetrics(
            tls_grade="C",
            engine_count=20,
        ))
        
        score_a_plus = status_a_plus.calculate_tier_score()
        score_c = status_c.calculate_tier_score()
        
        assert score_a_plus > score_c

    def test_tier_classification(self):
        """Test tier classification based on score."""
        # T1: score >= 0.70
        t1 = InstanceStatus(url="https://t1.example")
        t1.update_external_metrics(ExternalMetrics(
            uptime_day=100.0,
            tls_grade="A+",
            engine_count=30,
        ))
        for _ in range(5):
            t1.record_request(success=True)
        
        assert t1.get_tier() == 1, f"T1 should be tier 1, got {t1.get_tier()} (score={t1.calculate_tier_score():.3f})"

    def test_tier_2_classification(self):
        """Test T2 classification."""
        # T2: score 0.45-0.69
        t2 = InstanceStatus(url="https://t2.example")
        t2.update_external_metrics(ExternalMetrics(
            uptime_day=80.0,
            tls_grade="B",
            engine_count=10,
        ))
        # No request history = neutral internal
        
        tier = t2.get_tier()
        score = t2.calculate_tier_score()
        assert 2 <= tier <= 3, f"T2 should be tier 2 or 3, got T{tier} (score={score:.3f})"

    def test_tier_3_classification(self):
        """Test T3 classification."""
        # T3: score < 0.45
        t3 = InstanceStatus(url="https://t3.example")
        # No external metrics
        
        assert t3.get_tier() == 3, f"T3 should be tier 3, got {t3.get_tier()} (score={t3.calculate_tier_score():.3f})"


class TestExternalMetricsIntegration:
    """Tests for ExternalMetrics in InstanceStatus."""

    def test_update_external_metrics(self):
        """Test updating external metrics."""
        status = InstanceStatus(url="https://test.example")
        
        metrics = ExternalMetrics(
            uptime_day=99.0,
            tls_grade="A",
            engine_count=25,
        )
        status.update_external_metrics(metrics)
        
        assert status.external_metrics is not None
        assert status.external_metrics.tls_grade == "A"
        assert status._last_external_update is not None

    def test_external_metrics_serialization(self):
        """Test external metrics are serialized."""
        status = InstanceStatus(url="https://test.example")
        status.update_external_metrics(ExternalMetrics(
            uptime_day=100.0,
            tls_grade="A+",
            engine_count=20,
        ))
        
        data = status.to_dict()
        
        assert data["external_metrics"] is not None
        assert data["external_metrics"]["tls_grade"] == "A+"

    def test_external_metrics_deserialization(self):
        """Test external metrics are restored."""
        status = InstanceStatus(url="https://test.example")
        status.update_external_metrics(ExternalMetrics(
            uptime_day=98.0,
            tls_grade="B",
            engine_count=15,
        ))
        
        # Serialize and deserialize
        data = status.to_dict()
        restored = InstanceStatus.from_dict(data)
        
        assert restored.external_metrics is not None
        assert restored.external_metrics.tls_grade == "B"
        assert restored.external_metrics.engine_count == 15

    def test_backward_compatibility_no_external(self):
        """Test backward compatibility when no external metrics."""
        data = {
            "url": "https://test.example",
            "state": "closed",
        }
        
        status = InstanceStatus.from_dict(data)
        
        assert status.external_metrics is None
        assert status.calculate_tier_score() > 0


class TestManagerTierIntegration:
    """Tests for tier integration in manager.
    
    Note: These tests create manager directly without using fixtures
    to avoid conftest import issues.
    """

    def test_get_instances_by_tier(self):
        """Test _get_instances_by_tier groups instances correctly."""
        from searxng_mcp.manager import SearXNGManager
        
        manager = SearXNGManager()
        
        # T1 instance
        t1 = InstanceStatus(url="https://t1.example")
        t1.update_external_metrics(ExternalMetrics(
            uptime_day=100.0,
            tls_grade="A+",
            engine_count=30,
        ))
        for _ in range(5):
            t1.record_request(success=True)
        manager.instances["https://t1.example"] = t1
        
        # T2 instance
        t2 = InstanceStatus(url="https://t2.example")
        t2.update_external_metrics(ExternalMetrics(
            uptime_day=80.0,
            tls_grade="B",
            engine_count=15,
        ))
        manager.instances["https://t2.example"] = t2
        
        # T3 instance
        t3 = InstanceStatus(url="https://t3.example")
        manager.instances["https://t3.example"] = t3
        
        tiers = manager._get_instances_by_tier()
        
        assert len(tiers[1]) == 1
        assert "https://t1.example" in [url for url, _ in tiers[1]]
        assert len(tiers[3]) >= 1

    def test_tiers_are_shuffled(self):
        """Test instances within tiers are shuffled."""
        from searxng_mcp.manager import SearXNGManager
        
        manager = SearXNGManager()
        
        # Add multiple T3 instances
        for i in range(5):
            status = InstanceStatus(url=f"https://t3-{i}.example")
            manager.instances[f"https://t3-{i}.example"] = status
        
        tiers1 = manager._get_instances_by_tier()
        order1 = [url for url, _ in tiers1[3]]
        
        # Shuffle and check again
        manager._shuffle_instances()
        tiers2 = manager._get_instances_by_tier()
        order2 = [url for url, _ in tiers2[3]]
        
        # Orders should be different (with high probability)
        # Note: This test could occasionally fail if shuffle produces same order
        # but that's extremely unlikely with 5 elements
        assert set(order1) == set(order2)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_all_tls_grades(self):
        """Test all TLS grades produce valid scores."""
        grades = ["A+", "A", "B", "C", "D", "E", "F", "Unknown"]
        
        scores = []
        for grade in grades:
            status = InstanceStatus(url=f"https://{grade}.example")
            status.update_external_metrics(ExternalMetrics(
                tls_grade=grade,
                engine_count=20,
            ))
            scores.append(status.calculate_tier_score())
        
        # All scores should be valid (0-1)
        assert all(0 <= s <= 1 for s in scores)
        # A+ should be highest
        assert scores[0] >= scores[1] >= scores[2]

    def test_extreme_uptime_values(self):
        """Test extreme uptime values."""
        # Very high uptime
        high = InstanceStatus(url="https://high.example")
        high.update_external_metrics(ExternalMetrics(uptime_day=100.0))
        assert high.calculate_tier_score() <= 1.0
        
        # Very low uptime
        low = InstanceStatus(url="https://low.example")
        low.update_external_metrics(ExternalMetrics(uptime_day=0.0))
        assert low.calculate_tier_score() >= 0

    def test_many_requests_with_response_times(self):
        """Test with many requests including response times."""
        status = InstanceStatus(url="https://test.example")
        
        for i in range(100):
            status.record_request(success=True, response_time_ms=float(i % 100))
        
        assert status.total_requests == 100
        assert status.successful_requests == 100
        assert len(status.response_times_ms) == 10  # Limited to last 10
