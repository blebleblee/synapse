#!/usr/bin/env python3
"""
Automated Curriculum Generator for Learning Workspace
Iterates through lesson definitions, prompts the Gemini API,
and writes complete lesson artifacts directly to disk.
"""

import os
import sys
import time
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: 'google-genai' package is not installed.")
    print("Install it with: pip install google-genai")
    sys.exit(1)

# Support both Vertex AI (Company / Enterprise GCP) and Google AI Studio API Keys
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
GCP_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if GCP_PROJECT:
    print(f"[*] Authenticating via Vertex AI (Project: {GCP_PROJECT}, Location: {GCP_LOCATION})")
    client = genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)
elif API_KEY:
    print("[*] Authenticating via Gemini API Key")
    client = genai.Client(api_key=API_KEY)
else:
    print("Error: Neither GOOGLE_CLOUD_PROJECT (for Vertex AI / Enterprise) nor GEMINI_API_KEY was found.")
    print("Run: gcloud auth application-default login")
    print("Then: export GOOGLE_CLOUD_PROJECT='your-company-project-id'")
    sys.exit(1)


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = WORKSPACE_ROOT / "topics/computing_and_engineering/infrastructure_and_ops/kubernetes/harvester/artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_INSTRUCTION = """
You are Gemini Code Assist acting as a Senior Staff Engineer and Patient Mentor.
Generate an exhaustive, highly technical lesson in Markdown format.
Requirements:
1. Explain underlying architecture and kernel/hypervisor mechanics (cgroups, QEMU/KVM, namespaces, storage paths).
2. Provide complete, production-grade Kubernetes/KubeVirt/Harvester YAML manifests (no ellipses, no placeholders).
3. Include explicit Operational Lab verification steps with exact kubectl/virtctl commands and expected outputs.
4. Include critical operational safety warnings and failure domain considerations.
Output only clean Markdown without enclosing conversational filler.
"""

MODULES = [
    {
        "file": "lesson_03_installation.md",
        "title": "Lesson 3: Bare Metal Bootstrapping & Infrastructure as Code",
        "topic": "Harvester bare-metal ISO/iPXE boot flow, SLE Micro immutable Btrfs root, harvester-config.yaml schema, LACP bonding, VIP failover."
    },
    {
        "file": "lesson_05_networking.md",
        "title": "Lesson 5: Advanced Datacenter Networking with Multus & VLANs",
        "topic": "Multus CNI meta-plugin, Canal pod overlay vs host bridges, ClusterNetwork and VlanConfig CRDs, bridge vs masquerade binding, L2 trunking."
    },
    {
        "file": "lesson_06_vm_lifecycle.md",
        "title": "Lesson 6: Virtual Machine Lifecycle, Cloud-Init, and Advanced YAML",
        "topic": "KubeVirt VM/VMI state machine, NoCloud ISO metadata injection, CPU topologies (sockets/cores), qemu-guest-agent hooks, watchdog devices."
    },
    {
        "file": "lesson_07_rancher.md",
        "title": "Lesson 7: Multi-Cluster Management & RBAC via SUSE Rancher",
        "topic": "cattle-cluster-agent outbound WebSocket tunneling, Rancher Projects to Harvester Namespaces mapping, KubeVirt subresource RBAC, offline survivability."
    },
    {
        "file": "lesson_08_guest_clusters.md",
        "title": "Lesson 8: Kubernetes Inception (Guest Clusters & CSI/CCM Integration)",
        "topic": "Deploying RKE2 clusters on Harvester VMs via Rancher, Harvester Cloud Provider (CCM) for LoadBalancer VIPs, Harvester CSI driver for dynamic PVC provisioning."
    },
    {
        "file": "lesson_09_disaster_recovery.md",
        "title": "Lesson 9: Disaster Recovery, S3 Backups, and State Management",
        "topic": "Longhorn crash-consistent vs application-consistent snapshots via guest-agent fsfreeze, offloading delta blocks to S3/NFS backup targets, cross-cluster VM restoration."
    },
    {
        "file": "lesson_10_observability.md",
        "title": "Lesson 10: Deep Observability, Prometheus, and Kernel-level Troubleshooting",
        "topic": "Monitoring virt-launcher via kube-state-metrics and prometheus-operator, Grafana virtualization dashboards, troubleshooting virt-handler socket communication, kernel dmesg/kvm traces."
    }
]

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")

def generate_lesson(module):
    dest_path = ARTIFACTS_DIR / module["file"]
    print(f"\n==================================================")
    print(f"[*] Processing: {module['title']}")
    print(f"[*] Target File: {dest_path}")
    print(f"==================================================")

    prompt = f"""
Write the complete technical lesson for: {module['title']}
Focus areas: {module['topic']}
Format strictly in Markdown with headers, architecture diagrams, production YAML manifests, and an Operational Lab section.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
            ),
        )

        content = response.text
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[✔] Successfully generated and wrote: {dest_path.name} ({len(content)} bytes)")

    except Exception as e:
        print(f"[✘] Failed to generate {module['file']}: {e}")
        raise e

def main():
    print(f"Starting automated batch generation for Harvester curriculum...")
    print(f"Output directory: {ARTIFACTS_DIR}")

    for idx, module in enumerate(MODULES, 1):
        dest_file = ARTIFACTS_DIR / module["file"]
        if dest_file.exists() and dest_file.stat().st_size > 500:
            print(f"[↷] Skipping {module['file']} (already exists on disk)")
            continue

        generate_lesson(module)
        if idx < len(MODULES):
            print("[*] Waiting 5 seconds before next request...")
            time.sleep(5)

    print("\n[✔] All lessons have been generated and written directly to disk!")

if __name__ == "__main__":
    main()