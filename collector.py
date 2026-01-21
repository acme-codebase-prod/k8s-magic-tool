"""
Kubernetes inventory collector.

Collects nodes, pods, containers, and running processes from a Kubernetes cluster.
"""

import csv
import os
from typing import List, Dict, Any, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

class ConnectionError(Exception):
    """Raised when failing to connect to a Kubernetes cluster."""
    pass


class KubernetesInventoryCollector:
    """Collects inventory data from a Kubernetes cluster."""

    def __init__(self):
        """Initialize the collector and connect to the cluster."""
        self.v1_core = None
        self._connect()

    def _connect(self):
        """Connect to Kubernetes cluster using kubeconfig or ADC."""
        try:
            # Try in-cluster config first (for running in a pod)
            try:
                config.load_incluster_config()
            except config.ConfigException:
                # Fall back to kubeconfig
                config.load_kube_config()

            self.v1_core = client.CoreV1Api()
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Kubernetes cluster: {e}"
            )

    def collect_nodes(self) -> List[Dict[str, Any]]:
        """Collect all nodes."""
        try:
            nodes = self.v1_core.list_node()
            result = []
            for node in nodes.items:
                result.append({
                    "name": node.metadata.name,
                    "uid": node.metadata.uid,
                    "creation_timestamp": node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else None,
                    "kubernetes_version": node.status.node_info.kubelet_version if node.status.node_info else None,
                    "os_image": node.status.node_info.os_image if node.status.node_info else None,
                    "container_runtime": node.status.node_info.container_runtime_version if node.status.node_info else None,
                })
            return result
        except ApiException as e:
            raise RuntimeError(f"Failed to list nodes: {e}")

    def collect_pods(self) -> List[Dict[str, Any]]:
        """Collect all pods."""
        try:
            pods = self.v1_core.list_pod_for_all_namespaces()
            result = []
            for pod in pods.items:
                result.append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "uid": pod.metadata.uid,
                    "node_name": pod.spec.node_name if pod.spec else None,
                    "service_account": pod.spec.service_account_name if pod.spec else None,
                    "status": pod.status.phase if pod.status else None,
                    "pod_ip": pod.status.pod_ip if pod.status else None,
                })
            return result
        except ApiException as e:
            raise RuntimeError(f"Failed to list pods: {e}")

    def collect_containers(self) -> List[Dict[str, Any]]:
        """Collect all containers from all pods."""
        try:
            pods = self.v1_core.list_pod_for_all_namespaces()
            result = []
            for pod in pods.items:
                if not pod.spec or not pod.spec.containers:
                    continue

                for container in pod.spec.containers:
                    result.append({
                        "name": container.name,
                        "image": container.image,
                        "pod_name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "node_name": pod.spec.node_name if pod.spec else None,
                    })
            return result
        except ApiException as e:
            raise RuntimeError(f"Failed to list containers: {e}")

    def collect_processes(self, pod_name: str, namespace: str, container_name: Optional[str] = None) -> List[str]:
        """
        Collect running processes from a container using exec.

        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod
            container_name: Name of the container (optional, uses first container if not specified)

        Returns:
            List of process lines from ps command
        """
        try:
            # Get pod to find container name if not provided
            pod = self.v1_core.read_namespaced_pod(pod_name, namespace)

            if not pod.spec or not pod.spec.containers:
                return []

            if not container_name:
                container_name = pod.spec.containers[0].name

            # Check if pod is running
            if pod.status.phase != "Running":
                return []

            # Execute ps command in the container
            exec_command = ["ps", "aux"]
            resp = stream(
                self.v1_core.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                command=exec_command,
                container=container_name,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )

            # Parse ps output
            processes = [line.strip() for line in resp.split("\n") if line.strip()]
            return processes

        except ApiException:
            # Gracefully handle errors (container might not have ps, or exec might fail)
            return []
        except Exception:
            return []

    def collect_all_processes(self) -> List[Dict[str, Any]]:
        """Collect processes from all running pods."""
        try:
            pods = self.v1_core.list_pod_for_all_namespaces()
            result = []

            for pod in pods.items:
                if pod.status.phase != "Running":
                    continue

                if not pod.spec or not pod.spec.containers:
                    continue

                for container in pod.spec.containers:
                    processes = self.collect_processes(
                        pod.metadata.name,
                        pod.metadata.namespace,
                        container.name
                    )

                    result.append({
                        "pod_name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "container_name": container.name,
                        "processes": processes,
                    })

            return result
        except ApiException as e:
            raise RuntimeError(f"Failed to collect processes: {e}")

    def export_csv(self, data: Dict[str, List[Dict[str, Any]]], output_dir: str = "output"):
        """Export collected data to CSV files."""
        os.makedirs(output_dir, exist_ok=True)

        for key, items in data.items():
            if not items:
                continue

            filename = os.path.join(output_dir, f"{key}.csv")
            fieldnames = items[0].keys()

            with open(filename, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for item in items:
                    # Handle nested structures (like processes list)
                    row = {}
                    for field in fieldnames:
                        value = item.get(field)
                        if isinstance(value, list):
                            value = "\n".join(str(v) for v in value)
                        row[field] = value
                    writer.writerow(row)

            print(f"Exported {len(items)} {key} to {filename}")

