# Phase 7 — Kubernetes Deployment

## Objective

Deploy the Enterprise DevSecOps Platform application to a local Kubernetes cluster and move the application from standalone Docker execution to a Kubernetes-managed workload.

This phase introduces:

- Kubernetes workload orchestration
- Namespace isolation
- Declarative Deployment management
- Multiple application replicas
- Liveness and readiness probes
- CPU and memory resource controls
- Secure non-root container execution
- Kubernetes Service networking
- Application health validation
- Self-healing
- Horizontal scaling
- Runtime troubleshooting

---

## 1. Kubernetes Environment

The local Kubernetes environment uses:

- Docker Desktop
- Local Kubernetes cluster
- kubectl
- Kubernetes v1.36.1
- Single control-plane node
- Docker container runtime
- Local application images

The active Kubernetes context was verified using:

```powershell
kubectl config current-context
```

The active context was:

```text
docker-desktop
```

Cluster connectivity was verified using:

```powershell
kubectl get nodes
kubectl cluster-info
```

The Kubernetes control-plane node reached the `Ready` state.

This confirmed that the Kubernetes API server and local cluster were operational.

---

## 2. Dedicated Application Namespace

A dedicated namespace was created for the platform:

```text
enterprise-devsecops
```

Manifest:

```text
kubernetes/namespace.yaml
```

The namespace was applied using:

```powershell
kubectl apply -f kubernetes\namespace.yaml
```

Verification:

```powershell
kubectl get namespaces
```

The namespace reached:

```text
enterprise-devsecops   Active
```

### Why a Dedicated Namespace?

A namespace provides logical separation between application resources and other Kubernetes workloads.

All Phase 7 application resources are deployed inside:

```text
enterprise-devsecops
```

---

## 3. Kubernetes Deployment

The application workload is managed using a Kubernetes Deployment.

Manifest:

```text
kubernetes/deployment.yaml
```

Deployment name:

```text
enterprise-devsecops-app
```

The Deployment is configured with:

```yaml
replicas: 2
```

This instructs Kubernetes to maintain two application Pod replicas.

The manifest was validated using both client-side and server-side dry runs:

```powershell
kubectl apply --dry-run=client -f kubernetes\deployment.yaml
kubectl apply --dry-run=server -f kubernetes\deployment.yaml
```

The Deployment was then applied using:

```powershell
kubectl apply -f kubernetes\deployment.yaml
```

---

## 4. Container Image

The Kubernetes Deployment uses the application image:

```text
enterprise-devsecops-platform:1.0.1
```

The image contains the Flask application and its Waitress production WSGI runtime.

The Deployment uses:

```yaml
imagePullPolicy: IfNotPresent
```

This allows the local Kubernetes environment to use the application image when it is already available.

---

## 5. Application Port

The application container exposes:

```text
5000/TCP
```

The container port is assigned the name:

```text
http
```

Configuration:

```yaml
ports:
  - name: http
    containerPort: 5000
    protocol: TCP
```

Using a named port allows other Kubernetes configuration such as probes and Services to reference `http`.

---

## 6. Liveness Probe

A liveness probe was configured using the application's `/health` endpoint.

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

The liveness probe determines whether the application remains operational.

Conceptually:

```text
Application Container
        ↓
GET /health
        ↓
Healthy?
   ├── Yes → Continue running
   └── No  → Repeated failures can trigger recovery
```

---

## 7. Readiness Probe

A readiness probe was configured using:

```text
/ready
```

Configuration:

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

Readiness determines whether a Pod is ready to receive application traffic.

The difference is:

```text
Liveness
   ↓
Is the application alive?

Readiness
   ↓
Is the application ready to receive traffic?
```

---

## 8. Resource Requests and Limits

Resource controls were configured for the application container.

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

### Resource Requests

Configured requests:

```text
CPU:    100m
Memory: 128Mi
```

Requests provide Kubernetes with the minimum resource requirements used during scheduling.

### Resource Limits

Configured limits:

```text
CPU:    500m
Memory: 256Mi
```

Limits restrict the maximum CPU and memory allocation available to the application container.

This introduces basic resource governance for the workload.

---

## 9. Kubernetes Security Context

The application container uses a restricted security context.

```yaml
securityContext:
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  runAsUser: 100
  runAsGroup: 101
  capabilities:
    drop:
      - ALL
```

Security controls include:

- Non-root container execution
- Explicit runtime UID
- Explicit runtime GID
- Privilege escalation disabled
- Linux capabilities dropped

This extends the secure-container practices implemented earlier in the project into the Kubernetes runtime.

---

# Kubernetes Deployment Troubleshooting

The initial Kubernetes Deployment did not reach the `Running` state immediately.

Multiple infrastructure and container configuration issues were investigated systematically.

Rather than bypassing security controls or recreating the project, each failure was diagnosed at the layer where it occurred.

---

## 10. Issue 1 — Kubernetes API Context Not Available

Initially:

```powershell
kubectl get nodes
```

failed with an error similar to:

```text
Unable to connect to the server:
dial tcp [::1]:8080:
No connection could be made because the target machine actively refused it.
```

The context list was checked using:

```powershell
kubectl config get-contexts
kubectl config current-context
```

Initially, a usable Kubernetes context was not available.

After the local Kubernetes environment was initialized successfully, the active context became:

```text
docker-desktop
```

The cluster was then verified:

```powershell
kubectl get nodes
kubectl cluster-info
```

The control-plane node reached:

```text
Ready
```

### Learning

`kubectl` is a Kubernetes client.

It requires both:

```text
Valid kubeconfig context
          +
Reachable Kubernetes API server
```

before cluster commands can succeed.

---

## 11. Issue 2 — Pod Sandbox Creation Failure

After the Deployment was created, the initial Pods remained in:

```text
ContainerCreating
```

The Pods were inspected using:

```powershell
kubectl describe pod -n enterprise-devsecops
```

Kubernetes Events were inspected using:

```powershell
kubectl get events -n enterprise-devsecops --sort-by=.lastTimestamp
```

Events reported:

```text
FailedCreatePodSandBox
```

including errors such as:

```text
context deadline exceeded
```

and sandbox-name reservation failures.

The Pods had already been successfully assigned to:

```text
desktop-control-plane
```

This indicated that Kubernetes scheduling was working and the failure was occurring later in the Pod lifecycle.

The investigation therefore moved toward the Docker Desktop / container runtime / Pod sandbox layer.

---

## 12. Docker Desktop and WSL2 Recovery

During troubleshooting, Docker Desktop entered a stuck stopping state.

Docker Desktop status was checked using:

```powershell
docker desktop status
```

WSL state was checked using:

```powershell
wsl --list --verbose
```

A clean WSL shutdown was performed:

```powershell
wsl --shutdown
```

The WSL environments were then verified in the stopped state.

Docker Desktop was restarted:

```powershell
docker desktop start
```

Docker Engine health was tested using:

```powershell
docker run --rm hello-world
```

The successful `Hello from Docker!` response confirmed that the Docker daemon could again:

```text
Docker CLI
    ↓
Docker daemon
    ↓
Pull image
    ↓
Create container
    ↓
Execute container
```

Container DNS was also tested:

```powershell
docker run --rm alpine nslookup login.docker.com
```

DNS resolution succeeded.

After Docker Desktop and its runtime environment recovered, Kubernetes was able to progress beyond the Pod sandbox failure.

### Learning

A Pod stuck in `ContainerCreating` does not necessarily mean that the application itself is broken.

Possible layers include:

```text
Kubernetes Scheduler
        ↓
Container Runtime
        ↓
Pod Sandbox
        ↓
Container Image
        ↓
Container Configuration
        ↓
Application
```

Events helped identify which layer was failing.

---

## 13. Issue 3 — CreateContainerConfigError

After resolving the Pod sandbox problem, Kubernetes progressed further but the Pods entered:

```text
CreateContainerConfigError
```

The container security configuration included:

```yaml
runAsNonRoot: true
```

while the Docker image used a named account:

```text
appuser
```

Kubernetes could not automatically verify from the named user that the container would run with a non-root numeric UID.

Instead of removing `runAsNonRoot`, the runtime identity was verified directly from the application image.

UID verification:

```powershell
docker run --rm `
  --entrypoint id `
  enterprise-devsecops-platform:1.0.1 `
  -u
```

Result:

```text
100
```

GID verification:

```powershell
docker run --rm `
  --entrypoint id `
  enterprise-devsecops-platform:1.0.1 `
  -g
```

Result:

```text
101
```

The Deployment security context was therefore updated to explicitly use:

```yaml
runAsNonRoot: true
runAsUser: 100
runAsGroup: 101
```

### Learning

A named non-root Docker user and Kubernetes `runAsNonRoot` enforcement are related but separate mechanisms.

Using explicit numeric UID/GID values allows Kubernetes to enforce the intended runtime identity.

---

## 14. Issue 4 — Kubernetes YAML Hierarchy Error

While configuring the security context, it was initially placed under the resource limits block.

The incorrect logical structure was:

```yaml
resources:
  limits:
    cpu: "500m"
    memory: "256Mi"
    securityContext:
```

Kubernetes therefore attempted to interpret the `securityContext` object as a resource quantity.

Server-side validation reported:

```text
quantities must match the regular expression
```

The manifest hierarchy was corrected so that:

```text
resources
```

and:

```text
securityContext
```

are sibling properties of the container.

Correct structure:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"

securityContext:
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  runAsUser: 100
  runAsGroup: 101
  capabilities:
    drop:
      - ALL
```

The corrected manifest was validated using:

```powershell
kubectl apply --dry-run=client -f kubernetes\deployment.yaml
kubectl apply --dry-run=server -f kubernetes\deployment.yaml
```

### Learning

YAML can be syntactically valid while still describing an invalid Kubernetes object.

Indentation determines configuration hierarchy.

Server-side dry-run provides additional Kubernetes API validation before modifying the live workload.

---

## 15. Successful Kubernetes Rollout

After resolving the runtime identity and YAML hierarchy issues, the Deployment successfully reached:

```text
READY:       2/2
UP-TO-DATE:  2
AVAILABLE:   2
```

Verification:

```powershell
kubectl get deployments -n enterprise-devsecops
```

Pod verification:

```powershell
kubectl get pods -n enterprise-devsecops -o wide
```

Both application Pods reached:

```text
READY:  1/1
STATUS: Running
```

The workload structure became:

```text
Deployment
    ↓
ReplicaSet
    ↓
┌──────────────┐
│              │
▼              ▼
Pod 1          Pod 2
1/1 Running    1/1 Running
│              │
└──────┬───────┘
       ↓
Flask + Waitress
```

---

# Kubernetes Networking

## 16. ClusterIP Service

A Kubernetes Service was created to provide a stable network endpoint for the application.

Manifest:

```text
kubernetes/service.yaml
```

Service:

```text
enterprise-devsecops-service
```

Service type:

```text
ClusterIP
```

The final Service state included:

```text
PORT(S): 80/TCP
```

The traffic model is:

```text
ClusterIP Service :80
        ↓
Label Selector
        ↓
app=enterprise-devsecops-app
        ↓
┌─────────────┐
▼             ▼
Pod 1         Pod 2
:5000         :5000
```

The Service provides a stable endpoint even though individual Pod IP addresses can change.

---

## 17. Application Access Through Port Forwarding

Because `ClusterIP` is intended for internal cluster communication, local access was validated using port forwarding.

```powershell
kubectl port-forward `
  service/enterprise-devsecops-service `
  8080:80 `
  -n enterprise-devsecops
```

The request path became:

```text
Windows
localhost:8080
      ↓
kubectl port-forward
      ↓
ClusterIP Service :80
      ↓
Application Pod :5000
      ↓
Waitress
      ↓
Flask Application
```

---

## 18. Health Endpoint Validation

The health endpoint was tested using:

```powershell
Invoke-RestMethod http://localhost:8080/health
```

Successful response:

```text
service                       status
-------                       ------
enterprise-devsecops-platform healthy
```

This confirmed that application traffic successfully passed through the Kubernetes networking path.

---

## 19. Readiness Endpoint Validation

The readiness endpoint was tested using:

```powershell
Invoke-RestMethod http://localhost:8080/ready
```

Successful response:

```text
service                       status
-------                       ------
enterprise-devsecops-platform ready
```

The successful `/health` and `/ready` responses demonstrated that both runtime health and traffic readiness were functioning.

---

# Kubernetes Resilience

## 20. Self-Healing Validation

The Deployment was configured with:

```yaml
replicas: 2
```

Initially:

```text
Desired replicas: 2
Running Pods:     2
```

One application Pod was manually deleted:

```powershell
kubectl delete pod <POD_NAME> -n enterprise-devsecops
```

Kubernetes detected that the actual number of running replicas no longer matched the desired state.

The ReplicaSet automatically created a replacement Pod.

Observed lifecycle:

```text
Desired = 2
Actual  = 2
     ↓
One Pod deleted
     ↓
Actual = 1
     ↓
ReplicaSet detects difference
     ↓
Replacement Pod created
     ↓
Container starts
     ↓
Readiness succeeds
     ↓
Actual = 2
```

The replacement Pod received a new Pod name and Pod IP.

Final verification:

```powershell
kubectl get deployments -n enterprise-devsecops
kubectl get pods -n enterprise-devsecops -o wide
```

The Deployment returned to:

```text
READY:     2/2
AVAILABLE: 2
```

### Learning

Kubernetes continuously reconciles:

```text
Desired State
      ↕
Actual State
```

This is the foundation of Kubernetes self-healing.

---

## 21. Manual Horizontal Scaling

Horizontal workload scaling was tested by temporarily increasing the Deployment replica count.

Example:

```powershell
kubectl scale deployment/enterprise-devsecops-app `
  --replicas=4 `
  -n enterprise-devsecops
```

Kubernetes created additional application Pods to satisfy the new desired state.

The workload was verified using:

```powershell
kubectl get deployments -n enterprise-devsecops
kubectl get pods -n enterprise-devsecops
```

After completing the scaling validation, the Deployment was restored to:

```text
2 replicas
```

using:

```powershell
kubectl scale deployment/enterprise-devsecops-app `
  --replicas=2 `
  -n enterprise-devsecops
```

The final Deployment state returned to:

```text
READY:       2/2
UP-TO-DATE:  2
AVAILABLE:   2
```

### Learning

Manual scaling demonstrates Kubernetes desired-state reconciliation:

```text
Requested Replica Count
          ↓
Deployment Controller
          ↓
ReplicaSet
          ↓
Create/Delete Pods
          ↓
Actual = Desired
```

---

## 22. Final Manifest Validation

Before committing the Kubernetes configuration, all manifests were validated against the Kubernetes API server.

Namespace:

```powershell
kubectl apply --dry-run=server -f kubernetes\namespace.yaml
```

Result:

```text
namespace/enterprise-devsecops unchanged (server dry run)
```

Deployment:

```powershell
kubectl apply --dry-run=server -f kubernetes\deployment.yaml
```

Result:

```text
deployment.apps/enterprise-devsecops-app unchanged (server dry run)
```

Service:

```powershell
kubectl apply --dry-run=server -f kubernetes\service.yaml
```

Result:

```text
service/enterprise-devsecops-service unchanged (server dry run)
```

This confirms that the version-controlled Kubernetes manifests are accepted by the active Kubernetes API server.

---

## 23. Final Runtime State

The final namespace state was verified using:

```powershell
kubectl get all -n enterprise-devsecops
```

The final runtime state contained:

```text
Application Pods
    2 Running / Ready

ClusterIP Service
    enterprise-devsecops-service
    Port 80/TCP

Deployment
    READY:       2/2
    UP-TO-DATE:  2
    AVAILABLE:   2

Active ReplicaSet
    DESIRED: 2
    CURRENT: 2
    READY:   2
```

An older ReplicaSet remained with zero desired replicas.

This is expected Deployment behavior and preserves rollout history for Kubernetes Deployment management.

---

# Phase 7 Architecture

```text
                   Developer
                       │
                       ▼
               Kubernetes YAML
                       │
                       ▼
                Kubernetes API
                       │
                       ▼
                  Deployment
                       │
                       ▼
                  ReplicaSet
                       │
              ┌────────┴────────┐
              ▼                 ▼
            Pod 1             Pod 2
         1/1 Running       1/1 Running
              │                 │
              └────────┬────────┘
                       │
            Liveness + Readiness
                       │
                       ▼
                ClusterIP Service
                       │
                       ▼
               Flask + Waitress
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
              /     /health   /ready
```

---

# Security Controls Implemented

The Kubernetes workload now includes:

- Dedicated application namespace
- Non-root container execution
- Explicit UID/GID enforcement
- Privilege escalation disabled
- Linux capabilities dropped
- CPU requests
- CPU limits
- Memory requests
- Memory limits
- Liveness monitoring
- Readiness monitoring

---

# Troubleshooting Methodology

The troubleshooting process used during this phase followed a layered approach:

```text
kubectl get pods
       ↓
Identify workload state
       ↓
kubectl describe pod
       ↓
Inspect Kubernetes Events
       ↓
Identify failing layer
       ↓
┌─────────────────────────────┐
│ Kubernetes API              │
│ Scheduler                   │
│ Pod Sandbox                 │
│ Docker / WSL Runtime        │
│ Container Image             │
│ Security Context            │
│ Kubernetes Manifest         │
│ Application                 │
└─────────────────────────────┘
       ↓
Apply targeted correction
       ↓
Client-side validation
       ↓
Server-side validation
       ↓
Deploy
       ↓
Verify desired state
```

This approach avoids changing unrelated components before identifying the actual failing layer.

---

# Phase 7 Evidence

The following evidence was captured during implementation:

```text
screenshots/phase-07-01-kubernetes-cluster-ready.png
screenshots/phase-07-02-namespace-created.png
screenshots/phase-07-03-pod-sandbox-troubleshooting.png
screenshots/phase-07-04-kubernetes-deployment-running.png
screenshots/phase-07-05-kubernetes-service.png
screenshots/phase-07-06-kubernetes-application-access.png
screenshots/phase-07-07-kubernetes-self-healing.png
screenshots/phase-07-08-kubernetes-manual-scaling.png
screenshots/phase-07-09-kubernetes-final-state.png
```

Together, these screenshots provide evidence of:

- Cluster readiness
- Namespace creation
- Runtime troubleshooting
- Successful Deployment
- Kubernetes Service networking
- Application endpoint validation
- Kubernetes self-healing
- Horizontal scaling
- Final healthy Kubernetes state

---

# Phase 7 Outcome

Phase 7 successfully moved the Enterprise DevSecOps Platform from standalone Docker execution into a Kubernetes-managed application environment.

The implementation now demonstrates:

- Kubernetes cluster operation
- Namespace isolation
- Declarative Kubernetes manifests
- Deployment management
- ReplicaSet management
- Multiple application replicas
- Health monitoring
- Readiness management
- Resource governance
- Secure non-root execution
- Service discovery and networking
- Local application access
- Self-healing
- Horizontal scaling
- Kubernetes API validation
- Docker Desktop and WSL2 troubleshooting
- Pod sandbox troubleshooting
- Container security-context troubleshooting
- Kubernetes YAML troubleshooting

The final application path is:

```text
Docker Image
     ↓
Kubernetes Deployment
     ↓
ReplicaSet
     ↓
2 Application Pods
     ↓
Liveness + Readiness Probes
     ↓
ClusterIP Service
     ↓
Application Traffic
```

---

## Key Takeaway

Kubernetes is not simply being used to start containers in this project.

It is being used to declare and continuously maintain the desired application state.

Phase 7 demonstrates how Kubernetes manages application availability, health, networking, resource allocation, runtime security, replica recovery, and scaling.

The troubleshooting performed during this phase also demonstrates an important operational principle: identify the failing infrastructure layer using runtime evidence before applying a fix.