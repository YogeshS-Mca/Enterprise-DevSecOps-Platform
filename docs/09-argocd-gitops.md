# Phase 9 — Argo CD GitOps Continuous Delivery

## Objective

Implement GitOps-based continuous delivery for the Enterprise DevSecOps Platform using Argo CD.

The goal of this phase is to move Kubernetes deployment management from manual commands toward a Git-driven deployment model where the Git repository becomes the source of truth for the desired application state.

This phase introduces:

- Argo CD installation on Kubernetes
- Argo CD CLI access
- Git repository integration
- Helm chart deployment through Argo CD
- Declarative Argo CD Application configuration
- Automated synchronization
- Automatic pruning
- Self-healing
- Server-Side Apply
- Git-driven Kubernetes reconciliation

---

## Environment

The GitOps environment uses:

- Docker Desktop
- Local Kubernetes cluster
- Kubernetes v1.36.1
- kubectl
- Helm
- Argo CD
- Argo CD CLI
- GitHub
- Enterprise DevSecOps Platform Helm chart

The Kubernetes context used during this phase was:

```text
docker-desktop
```

The application namespace is:

```text
enterprise-devsecops
```

The Argo CD control-plane namespace is:

```text
argocd
```

---

## GitOps Architecture

The deployment workflow introduced in this phase is:

```text
Developer
    |
    v
Git Commit / Pull Request
    |
    v
GitHub Repository
    |
    v
Argo CD
    |
    v
Helm Chart
    |
    v
Kubernetes Deployment
    |
    v
Application Pods
```

Instead of manually changing the Kubernetes workload, the desired application configuration is stored in Git.

Argo CD continuously compares:

```text
Desired State in Git
        |
        v
Actual State in Kubernetes
```

When a difference is detected, Argo CD can reconcile the Kubernetes cluster with the configuration stored in Git.

---

## Pre-GitOps Cluster Validation

Before introducing Argo CD management, the existing Kubernetes environment was verified.

The active Kubernetes context was checked using:

```powershell
kubectl config current-context
```

The cluster nodes were verified using:

```powershell
kubectl get nodes
```

The existing application resources were checked using:

```powershell
kubectl get all -n enterprise-devsecops
```

The existing Helm release was also verified:

```powershell
helm list -n enterprise-devsecops
```

The application was healthy with two running replicas before GitOps configuration was introduced.

This provided a known-good baseline before moving deployment management to Argo CD.

---

## Argo CD Installation

Argo CD was installed into a dedicated Kubernetes namespace:

```text
argocd
```

After installation, the Argo CD components were verified using:

```powershell
kubectl get pods -n argocd -o wide
```

The major Argo CD components were successfully running, including:

```text
argocd-application-controller
argocd-applicationset-controller
argocd-dex-server
argocd-notifications-controller
argocd-redis
argocd-repo-server
argocd-server
```

All required Argo CD components reached the `Running` state.

---

## Argo CD CLI Installation

The Argo CD CLI was installed on Windows using WinGet.

The available package was identified using:

```powershell
winget search ArgoCD
```

The correct package ID was:

```text
argoproj.argocd
```

The CLI was installed using:

```powershell
winget install --id argoproj.argocd -e
```

The installation was validated using:

```powershell
argocd version --client
```

The installed client version was:

```text
v3.5.1
```

---

## Argo CD Access Validation

After accessing the Argo CD server, authentication was verified using:

```powershell
argocd account get-user-info
```

The CLI confirmed:

```text
Logged In: true
Username: admin
Issuer: argocd
```

Cluster connectivity was checked using:

```powershell
argocd cluster list
```

Argo CD identified the local Kubernetes cluster as:

```text
https://kubernetes.default.svc
```

This confirmed that Argo CD could communicate with the Kubernetes API server.

---

## Declarative Argo CD Application

A declarative Argo CD Application manifest was created at:

```text
argocd/application.yaml
```

The Application definition is:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application

metadata:
  name: enterprise-devsecops
  namespace: argocd

spec:
  project: default

  source:
    repoURL: https://github.com/YogeshS-Mca/Enterprise-DevSecOps-Platform.git
    targetRevision: main
    path: helm/enterprise-devsecops

    helm:
      releaseName: enterprise-devsecops

  destination:
    server: https://kubernetes.default.svc
    namespace: enterprise-devsecops

  syncPolicy:
    automated:
      prune: true
      selfHeal: true

    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
```

This manifest connects Argo CD to the Helm chart stored in the GitHub repository.

---

## Application Source Configuration

The Git repository used by Argo CD is:

```text
Enterprise-DevSecOps-Platform
```

The tracked Git revision is:

```text
main
```

The Helm chart path is:

```text
helm/enterprise-devsecops
```

The Helm release name is:

```text
enterprise-devsecops
```

Therefore, Argo CD uses the Helm chart stored on the `main` branch as the desired state of the application.

---

## Destination Configuration

The Application deploys to the Kubernetes API server:

```text
https://kubernetes.default.svc
```

and targets the namespace:

```text
enterprise-devsecops
```

The namespace can also be created automatically through:

```yaml
syncOptions:
  - CreateNamespace=true
```

---

## Argo CD Application Validation

Before creating the Application, the manifest was validated locally:

```powershell
kubectl apply --dry-run=client -f argocd\application.yaml
```

The Kubernetes API server was then used for additional validation:

```powershell
kubectl apply --dry-run=server -f argocd\application.yaml
```

The validation completed successfully.

The Helm chart was also validated using:

```powershell
helm lint helm\enterprise-devsecops
```

Result:

```text
1 chart(s) linted, 0 chart(s) failed
```

The chart was rendered using:

```powershell
helm template enterprise-devsecops helm\enterprise-devsecops
```

These checks helped validate both the Argo CD Application manifest and the underlying Helm chart before synchronization.

---

## Creating the Argo CD Application

The Application was created using:

```powershell
kubectl apply -f argocd\application.yaml
```

The created Application was verified using:

```powershell
kubectl get applications -n argocd
```

Additional application information was retrieved using:

```powershell
argocd app get enterprise-devsecops
```

The Application successfully detected:

```text
Repository: https://github.com/YogeshS-Mca/Enterprise-DevSecOps-Platform.git
Target Revision: main
Path: helm/enterprise-devsecops
Destination Namespace: enterprise-devsecops
```

---

## Initial OutOfSync State

After the Argo CD Application was created, its status was checked using:

```powershell
kubectl get application enterprise-devsecops `
  -n argocd `
  -o wide
```

The initial status showed:

```text
SYNC STATUS: OutOfSync
HEALTH STATUS: Healthy
```

This was an important GitOps observation.

`Healthy` indicated that the existing Kubernetes workload itself was functioning correctly.

`OutOfSync` indicated that the live Kubernetes state did not completely match the desired state rendered by Argo CD from Git.

This demonstrates that application health and Git synchronization are separate concepts.

---

## First GitOps Synchronization

The first Argo CD synchronization aligned the existing Kubernetes resources with the desired state stored in Git.

After synchronization, the Application reached:

```text
Sync Status: Synced
Health Status: Healthy
```

The managed resources included:

```text
Namespace
Service
Deployment
```

This established Argo CD as the GitOps deployment controller for the application.

---

## Server-Side Apply

The following synchronization option was enabled:

```yaml
syncOptions:
  - ServerSideApply=true
```

Server-Side Apply allows Kubernetes to manage field ownership through the API server.

This is particularly relevant to this project because the application resources had previously been managed using:

```text
kubectl
        ↓
Helm
        ↓
Argo CD
```

The project therefore demonstrates a realistic migration of Kubernetes resource management across multiple deployment mechanisms.

---

## Automated Synchronization

Automated synchronization was enabled using:

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```

This changes the deployment model from manual synchronization to continuous GitOps reconciliation.

The desired workflow becomes:

```text
Git change
    |
    v
Argo CD detects difference
    |
    v
Application becomes OutOfSync
    |
    v
Automatic synchronization
    |
    v
Kubernetes reconciled
    |
    v
Application returns to Synced / Healthy
```

---

## Automatic Pruning

Pruning was enabled using:

```yaml
prune: true
```

With pruning enabled, resources removed from the Git-managed desired state can also be removed from the Kubernetes cluster during synchronization.

This helps prevent obsolete resources from remaining in the cluster after they are removed from the declarative configuration.

---

## Self-Healing

Self-healing was enabled using:

```yaml
selfHeal: true
```

Self-healing allows Argo CD to detect changes made directly to managed Kubernetes resources and reconcile them back to the desired state stored in Git.

The intended control model is:

```text
Git = Desired State
Kubernetes = Actual State
Argo CD = Reconciliation Controller
```

If the actual cluster state drifts from Git, Argo CD can restore the Git-defined configuration.

---

## Automated Sync Policy Verification

The configured synchronization policy was verified using:

```powershell
kubectl get application enterprise-devsecops `
  -n argocd `
  -o jsonpath="{.spec.syncPolicy}"
```

The result confirmed:

```json
{
  "automated": {
    "prune": true,
    "selfHeal": true
  },
  "syncOptions": [
    "CreateNamespace=true",
    "ServerSideApply=true"
  ]
}
```

The Argo CD Application also reported:

```text
Sync Policy: Automated (Prune)
Sync Status: Synced
Health Status: Healthy
```

This confirmed that automated GitOps reconciliation was enabled successfully.

---

## Git-Driven Replica Change

To demonstrate Git-driven deployment, the Helm desired state was changed from:

```yaml
replicaCount: 2
```

to:

```yaml
replicaCount: 3
```

The change was made in:

```text
helm/enterprise-devsecops/values.yaml
```

Before the Git change was merged into the tracked `main` branch, the running Kubernetes Deployment remained:

```text
READY: 2/2
```

This behavior is expected.

The Argo CD Application tracks:

```yaml
targetRevision: main
```

Therefore, a change existing only on the feature branch does not become the desired production state until it is merged into `main`.

The intended GitOps validation flow is:

```text
Feature Branch
      |
      v
replicaCount: 3
      |
      v
Pull Request
      |
      v
Merge into main
      |
      v
Argo CD detects new Git revision
      |
      v
Automatic synchronization
      |
      v
Deployment scales from 2 to 3 replicas
```

This demonstrates an important GitOps principle:

> Changes should flow through Git rather than being applied directly to the cluster.

---

## GitOps Validation Strategy

The Phase 9 implementation is validated through several layers:

```text
1. Kubernetes cluster validation
        |
        v
2. Argo CD component validation
        |
        v
3. Argo CD CLI authentication
        |
        v
4. Application manifest validation
        |
        v
5. Helm lint and rendering
        |
        v
6. Argo CD Application creation
        |
        v
7. Initial OutOfSync detection
        |
        v
8. Successful synchronization
        |
        v
9. Automated sync configuration
        |
        v
10. Git-driven desired-state change
        |
        v
11. Automatic Kubernetes reconciliation
```

---

## Screenshots

Evidence captured during this phase includes:

```text
phase-09-01-pre-gitops-cluster-state.png
phase-09-01-argocd-application-validation.png
phase-09-02-argocd-components-running.png
phase-09-03-argocd-dashboard.png
phase-09-04-argocd-cli-access.png
phase-09-05-argocd-application-outofsync.png
phase-09-06-first-gitops-sync-success.png
phase-09-07-argocd-automated-sync-enabled.png
phase-09-07-argocd-synced-healthy-dashboard.png
```

Additional evidence will be captured after the Git-driven replica change is merged and automatically reconciled by Argo CD.

---

## Key Learning

This phase demonstrates the transition from imperative deployment management to declarative GitOps-based continuous delivery.

The previous deployment model was:

```text
Developer
    |
    v
kubectl / Helm command
    |
    v
Kubernetes
```

The GitOps deployment model is:

```text
Developer
    |
    v
Git Commit
    |
    v
Pull Request
    |
    v
main Branch
    |
    v
Argo CD
    |
    v
Helm
    |
    v
Kubernetes
```

The most important principle is:

```text
Git defines the desired state.
Argo CD continuously compares desired and actual state.
Kubernetes executes the reconciled workload.
```

---

## Phase 9 Current Status

The following capabilities have been implemented successfully:

- Argo CD installed in Kubernetes
- Argo CD components running
- Argo CD CLI installed
- CLI authentication verified
- Kubernetes cluster connectivity verified
- Declarative Argo CD Application created
- GitHub repository configured as application source
- Helm chart configured as deployment source
- Initial OutOfSync state observed
- First GitOps synchronization completed
- Application reached Synced and Healthy state
- Automated synchronization enabled
- Automatic pruning enabled
- Self-healing enabled
- Server-Side Apply enabled
- Git-driven replica change prepared

The final validation is to merge the desired replica change into `main` and verify that Argo CD automatically reconciles the Kubernetes Deployment from two replicas to three without manually running `kubectl apply`, `helm upgrade`, or `argocd app sync`.