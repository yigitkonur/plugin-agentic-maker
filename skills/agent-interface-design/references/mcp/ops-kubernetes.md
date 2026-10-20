# Deploy a remote MCP server on Kubernetes

> Read when: you are running a Streamable HTTP MCP server as a Kubernetes service and need rollout, autoscaling, affinity and shutdown settings.

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#12. Kubernetes Deployment for MCP Servers -->
## Roll out with zero downtime, scale horizontally, drain on SIGTERM

Remote servers running as HTTP services need rolling updates, horizontal scaling and proper resource limits. Without a proper rolling update config, deployments interrupt active agent sessions and corrupt in-progress tool calls.

Deployment manifest (the one reference example):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  labels:
    app: mcp-server
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0          # Zero-downtime: never reduce below desired count
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: your-registry/mcp-server:latest
        ports:
        - containerPort: 3000
        env:
        - name: MCP_SESSION_SECRET
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: session-secret
        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            cpu: "1000m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

Session affinity for stateful servers: set the Service to `sessionAffinity: ClientIP` with `sessionAffinityConfig.clientIP.timeoutSeconds: 3600` (1 hour stickiness). Alternatively externalize session state to Redis and drop the affinity requirement, which enables true horizontal scalability (see [ops-session-state.md](ops-session-state.md)). The affinity snippet is in the [typescript framework file](../frameworks/mcp-ts/transport-and-ops.md).

Graceful shutdown: handle SIGTERM by stopping new connections (`server.close()`), waiting for active tool calls to complete (drain in-flight), then exiting 0. Code: [typescript](../frameworks/mcp-ts/transport-and-ops.md).

Related: [../decisions/scaling.md](../decisions/scaling.md), [ops-hosting-constraints.md](ops-hosting-constraints.md), [ops-observability.md](ops-observability.md) (probe endpoints).

Sources: Stacklok, modelcontextprotocol.io deployment guide.
