# Lesson 3: RBAC in Distributed Infrastructure: Kubernetes, IAM, Service Meshes

## 1. First-Principles Intuition & Invariants

Authorization is fundamentally a question of correspondence: does the identity making a request have a sanctioned relationship to the resource it is trying to act upon? In a monolithic application running on a single host, that correspondence is simple enough to reason about manually. In a distributed system spanning hundreds of microservices, thousands of pods, and multiple cloud provider accounts, the problem becomes a matter of formal policy enforcement at every layer of the stack simultaneously. RBAC — Role-Based Access Control — is the dominant answer the industry has converged on, not because it is theoretically perfect, but because it maps cleanly onto how organizations actually model authority: people and workloads belong to roles, and roles carry permissions.

The invariant that RBAC enforces is the principle of least privilege expressed through indirection. Rather than binding permissions
