# k8s-magic-tool

A simple Kubernetes inventory collection tool that collects nodes, pods, containers, and optionally running processes from a Kubernetes cluster.

## Features

- Collects all nodes, pods, and containers
- Optionally collects running processes from containers via exec
- Exports data to CSV format
- Simple, minimal codebase
- Tests that verify cluster connectivity

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the script directly (no installation needed):

```bash
# Basic inventory collection
python run_inventory.py

# Include process collection (slower)
python run_inventory.py --include-processes

# Specify output directory
python run_inventory.py --output-dir /tmp/inventory
```

## Authentication

The tool uses standard Kubernetes authentication:

- **kubeconfig**: Uses your default kubeconfig file (`~/.kube/config`)
- **Application Default Credentials**: Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable with path to service account JSON key

## Output

The tool creates CSV files in the `output/` directory (or specified directory):

- `nodes.csv` - All cluster nodes
- `pods.csv` - All pods with namespace, node, service account
- `containers.csv` - All containers with image, pod, namespace
- `processes.csv` - Running processes from containers (if `--include-processes` is used)

## Testing

```bash
pytest
```

Tests verify that:
- Authentication to Kubernetes cluster works
- API calls to list nodes and pods succeed

Tests gracefully skip if the cluster is not reachable.

