"""
Tests for Kubernetes inventory collector.

These tests attempt to connect to a real Kubernetes cluster.
They gracefully fail with clear errors if the cluster is not reachable.
"""

import pytest
import sys
import os

# Add parent directory to path so we can import collector
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collector import KubernetesInventoryCollector, ConnectionError
from kubernetes.client.rest import ApiException


def _get_collector_or_skip() -> KubernetesInventoryCollector:
    """Get collector or skip test if connection fails."""
    try:
        return KubernetesInventoryCollector()
    except ConnectionError as e:
        pytest.fail(
            f"Cannot connect to cluster: {e}. "
            "Make sure kubeconfig or GOOGLE_APPLICATION_CREDENTIALS is set."
        )


def test_can_connect_and_list_nodes():
    """Test that we can connect and list nodes."""
    collector = _get_collector_or_skip()
    try:
        resp = collector.v1_core.list_node(_preload_content=False, limit=1)
        assert resp is not None
    except ApiException as e:
        pytest.fail(f"Failed to list nodes via Kubernetes API: {e}")


def test_can_connect_and_list_pods():
    """Test that we can connect and list pods."""
    collector = _get_collector_or_skip()
    try:
        resp = collector.v1_core.list_pod_for_all_namespaces(
            _preload_content=False, limit=1
        )
        assert resp is not None
    except ApiException as e:
        pytest.fail(f"Failed to list pods via Kubernetes API: {e}")

