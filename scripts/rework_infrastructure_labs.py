#!/usr/bin/env python3
"""
Targeted Rework for Infrastructure Labs
Replaces generic kernel/eBPF stubs with authentic, topic-specific masterclass labs.
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.models import AnthropicProvider, validate_generation_output

if not os.getenv("ANTHROPIC_API_KEY"):
    print("[✘] Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
    sys.exit(1)

TARGETS = [
    {
        "subtopic": "sre",
        "title": "Site Reliability Engineering (SRE) & Kubernetes Operations",
        "focus": "SLI/SLO measurement, Prometheus PromQL alerting, Error Budgets, PodDisruptionBudgets, Chaos Engineering (node drain, pod kills, latency injection), Incident Triage, and Post-Mortem Diagnostics. Do NOT write generic eBPF labs.",
        "tools": "kubectl, prometheus-operator, alertmanager, hey/k6 (load testing), chaos-mesh or litmus"
    },
    {
        "subtopic": "devops",
        "title": "DevOps Engineering & Continuous Delivery Pipelines",
        "focus": "CI/CD pipeline automation, Docker BuildKit multi-stage optimization, container vulnerability scanning (Trivy), GitOps deployment, Helm chart packaging, and blue-green/canary rollout verification. Do NOT write generic eBPF labs.",
        "tools": "docker, trivy, helm, git, act/gh, kubectl"
    },
    {
        "subtopic": "automation",
        "title": "Systems Automation & Configuration Management",
        "focus": "Idempotent configuration management, Ansible playbooks and inventory verification, Terraform infrastructure state inspection, systemd service automation, and scheduled automated maintenance. Do NOT write generic eBPF labs.",
        "tools": "ansible, ansible-playbook, terraform, systemctl, journalctl"
    },
    {
        "subtopic": "harvester",
        "title": "Harvester Open-Source Hyperconverged Infrastructure",
        "focus": "KubeVirt virtual machine lifecycle on Kubernetes, Longhorn distributed block storage replication, Multus CNI VLAN bridge networking, and VM migration diagnostics. Do NOT write generic eBPF labs.",
        "tools": "kubectl, virtctl, longhorn-ctl, ip link"
    },
    {
        "subtopic": "hyperconverged_infrastructure",
        "title": "Hyperconverged Infrastructure (HCI) & Storage Virtualization",
        "focus": "Converged compute and software-defined storage (Ceph / Longhorn / vSAN architecture), storage pool rebalancing, quorum consensus under split-brain testing, and live hypervisor failover. Do NOT write generic eBPF labs.",
        "tools": "ceph, rbd, kubectl, fio, iperf3"
    },
    {
        "subtopic": "infrastructure",
        "title": "Core Systems Infrastructure & Linux System Administration",
        "focus": "Linux system administration, storage volume management (LVM, RAID), systemd target state machines, network bonding/VLANs, and resource limits (cgroups v2, systemd slices). Do NOT write generic eBPF labs.",
        "tools": "systemctl, lvm, mdadm, ip, journalctl, free, lsblk"
    }
]

def main():
    p = AnthropicProvider(model="claude-sonnet-5")
    print(f"[*] Starting targeted labs rework with {p.model} across {len(TARGETS)} infrastructure topics...")

    for item in TARGETS:
        slug = item["subtopic"]
        title = item["title"]
        focus = item["focus"]
        tools = item["tools"]
        out_path = WORKSPACE_ROOT / "topics" / "computing" / "infrastructure" / slug / "labs.md"
        
        if not out_path.resolve().is_relative_to(WORKSPACE_ROOT):
            print(f"[✘] Security: Skipping {slug}, path escapes workspace root", file=sys.stderr)
            continue
            
        out_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n==================================================")
        print(f"[*] Authoring dedicated labs for: {slug} ({title})...")
        print(f"==================================================")

        prompt = f"""You are an elite staff infrastructure engineer and author (O'Reilly / MIT Press standard).
Write the complete, production-grade operational verification labs (labs.md) specifically for '{title}'.

CORE TOPIC FOCUS:
{focus}

PRIMARY TOOLCHAIN:
{tools}

OBJECTIVES:
1. FOCUS: Hands-on operational verification strictly tailored to {title}. Every exercise must relate directly to this discipline.
2. ABSOLUTE PROHIBITION: DO NOT write a generic kernel eBPF lab (do NOT mention or focus on bpftool or kernel page cache). Focus on real production tools ({tools}).
3. Include production-grade, executable configuration files, manifests, and CLI commands with deep first-principles explanations.
4. Include valid Mermaid.js diagrams with proper subgraph IDs (subgraph sub_id ["Title"]).
5. Output the complete raw Markdown document starting directly with '# Operational Verification Labs: {title}'. No preambles or outer code fences.
"""

        t0 = time.time()
        for attempt in range(1, 4):
            chunks = []
            sys.stdout.write(f"  [~] Streaming tokens (attempt {attempt}/3): ")
            sys.stdout.flush()
            try:
                for chunk in p.generate_stream(prompt, system_instruction=f"You are a master staff engineer specializing in {title}.", max_tokens=8192):
                    chunks.append(chunk)
                    sys.stdout.write(".")
                    sys.stdout.flush()

                raw = "".join(chunks)
                validated = validate_generation_output(raw)
                
                if not validated or len(validated.strip()) < 500:
                    raise ValueError("Generated output is too short or empty")
                
                if out_path.exists():
                    backup_path = out_path.with_suffix(f".md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    backup_path.write_text(out_path.read_text(encoding="utf-8"), encoding="utf-8")
                    
                out_path.write_text(validated.strip() + "\n", encoding="utf-8")
                elapsed = time.time() - t0
                lines = len(validated.splitlines())
                print(f"\n  [✔] Successfully generated {slug}/labs.md ({lines} lines in {elapsed:.1f}s)!")
                break
            except Exception as e:
                print(f"\n  [✘] Attempt {attempt} failed for {slug}: {e}")
                if attempt < 3:
                    time.sleep(attempt * 4)
                else:
                    print(f"  [✘] Skipping {slug} after 3 failures.", file=sys.stderr)

    print("\n[✔] All targeted infrastructure labs reworked successfully!")

if __name__ == "__main__":
    main()
