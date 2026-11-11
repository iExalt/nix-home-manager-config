# Kubernetes workloads

- Before applying a test Pod for a specific node, inspect its live taints and
  labels and adapt the scheduling fields from a running workload there. A
  server-side dry-run does not prove the Pod can schedule.
- Before relying on a cached private image, confirm the probe can use it with
  its own approved pull credentials and policy; the node's image inventory
  alone does not prove access.
