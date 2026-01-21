#!/usr/bin/env python3
"""Kubernetes inventory collection script.

Example:
    python run_inventory.py --include-processes
    python run_inventory.py --output-dir /tmp/inventory
"""

import sys
import argparse
from collector import KubernetesInventoryCollector


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Collect Kubernetes cluster inventory"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for inventory files (default: output)"
    )
    parser.add_argument(
        "--include-processes",
        action="store_true",
        help="Collect running processes from containers (slower)"
    )

    args = parser.parse_args()

    try:
        print("Connecting to Kubernetes cluster...")
        collector = KubernetesInventoryCollector()

        print("Collecting nodes...")
        nodes = collector.collect_nodes()
        print(f"  Found {len(nodes)} nodes")

        print("Collecting pods...")
        pods = collector.collect_pods()
        print(f"  Found {len(pods)} pods")

        print("Collecting containers...")
        containers = collector.collect_containers()
        print(f"  Found {len(containers)} containers")

        data = {
            "nodes": nodes,
            "pods": pods,
            "containers": containers,
        }

        if args.include_processes:
            print("Collecting processes from running containers...")
            processes = collector.collect_all_processes()
            print(f"  Collected processes from {len(processes)} containers")
            data["processes"] = processes

        print(f"\nExporting CSV files to {args.output_dir}...")
        collector.export_csv(data, args.output_dir)

        print("\nInventory collection complete!")

    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nMake sure you have:")
        print("  - Valid kubeconfig file, or")
        print("  - GOOGLE_APPLICATION_CREDENTIALS environment variable set", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

