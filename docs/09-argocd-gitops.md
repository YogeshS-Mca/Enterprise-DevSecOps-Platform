# Phase 9 — Argo CD GitOps Continuous Delivery

## Objective

Implement GitOps-based continuous delivery for the Enterprise DevSecOps Platform using Argo CD.

The goal of this phase is to move Kubernetes deployment management from manual deployment commands toward a Git-driven delivery model where the Git repository becomes the source of truth for the desired application state.

This phase implements:

- Argo CD on Kubernetes
- Argo CD CLI access
- GitHub repository integration
- Helm deployment through Argo CD
- Declarative Argo CD Application configuration
- Automated synchronization
- Automatic pruning
- Self-healing
- Server-Side Apply
- Git-driven Kubernetes reconciliation
- Pull Request-based deployment changes
- Configuration-drift detection and recovery

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

Application namespace:

```text
enterprise-devsecops
```

Argo CD control-plane namespace:

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
Feature Branch
    |
    v
Git Commit
    |
    v
Pull Request
    |
    v
GitHub main Branch
    |
    v
Argo CD
    |
    v
Helm Chart
    |
    v
Kubernetes
    |
    v
Deployment + Service
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

When differences are detected, Argo CD reconciles the Kubernetes environment toward the desired state stored in Git.

---

## Pre-GitOps Cluster Validation

Before introducing Argo CD, the existing Kubernetes environment was verified.

The current Kubernetes context was checked using:

```powershell
kubectl config current-context
```

Cluster nodes were verified using:

```powershell
kubectl get nodes
```

Existing application resources were checked using:

```powershell
kubectl get all -n enterprise-devsecops
```

The existing Helm release was verified using:

```powershell
helm list -n enterprise-devsecops
```

The application was healthy with two running replicas before GitOps management was introduced.

This provided a known-good baseline before moving deployment control to Argo CD.

### Evidence

```text
screenshots/phase-09-01-pre-gitops-cluster-state.png
```

---

## Argo CD Installation

Argo CD was installed into a dedicated Kubernetes namespace:

```text
argocd
```

The Argo CD components were verified using:

```powershell
kubectl get pods -n argocd -o wide
```

The major components included:

```text
argocd-application-controller
argocd-applicationset-controller
argocd-dex-server
argocd-notifications-controller
argocd-redis
argocd-repo-server
argocd-server
```

All required Argo CD components successfully reached the `Running` state.

### Evidence

```text
screenshots/phase-09-02-argocd-components-running.png
```

---

## Argo CD Dashboard Access

The Argo CD API server was exposed locally using Kubernetes port forwarding.

Example:

```powershell
kubectl port-forward svc/argocd-server `
  -n argocd `
  8080:443
```

The dashboard was then available locally through HTTPS.

Successful access to the Argo CD login interface confirmed connectivity to the Argo CD server.

### Evidence

```text
screenshots/phase-09-03-argocd-dashboard.png
```

---

## Argo CD CLI Installation

The Argo CD CLI was installed on Windows using WinGet.

The package was identified using:

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

Installation was validated using:

```powershell
argocd version --client
```

Installed client version:

```text
v3.5.1
```

---

## Argo CD CLI Authentication

Authentication was verified using:

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

This confirmed that the Argo CD CLI and control plane could communicate successfully with the Kubernetes environment.

### Evidence

```text
screenshots/phase-09-04-argocd-cli-access.png
```

---

## Declarative Argo CD Application

A declarative Application manifest was created at:

```text
argocd/application.yaml
```

The final configuration is:

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

The Application connects Argo CD to the Helm chart stored in the Git repository.

The tracked branch is:

```text
main
```

The Helm chart path is:

```text
helm/enterprise-devsecops
```

The destination namespace is:

```text
enterprise-devsecops
```

---

## Application Manifest Validation

Before applying the Application manifest, client-side validation was performed:

```powershell
kubectl apply --dry-run=client -f argocd\application.yaml
```

Server-side validation was then performed:

```powershell
kubectl apply --dry-run=server -f argocd\application.yaml
```

Both validations completed successfully.

The Helm chart was also validated:

```powershell
helm lint helm\enterprise-devsecops
```

Result:

```text
1 chart(s) linted, 0 chart(s) failed
```

The Helm templates were rendered using:

```powershell
helm template enterprise-devsecops `
  helm\enterprise-devsecops
```

These validation layers reduced the risk of introducing an invalid GitOps configuration.

### Evidence

```text
screenshots/phase-09-01-argocd-application-validation.png
```

---

## Creating the Argo CD Application

The Application was created using:

```powershell
kubectl apply -f argocd\application.yaml
```

The resource was verified using:

```powershell
kubectl get applications -n argocd
```

Detailed information was retrieved using:

```powershell
argocd app get enterprise-devsecops
```

Argo CD successfully detected:

```text
Repository:
Enterprise-DevSecOps-Platform

Target Revision:
main

Path:
helm/enterprise-devsecops

Destination:
enterprise-devsecops
```

---

## Initial OutOfSync Detection

After the Application was created, its state was checked using:

```powershell
kubectl get application enterprise-devsecops `
  -n argocd `
  -o wide
```

The initial result showed:

```text
Sync Status: OutOfSync
Health Status: Healthy
```

This demonstrated an important GitOps concept.

`Healthy` indicated that the existing Kubernetes application was operational.

`OutOfSync` indicated that the actual Kubernetes configuration did not fully match the desired state rendered by Argo CD from Git.

Therefore:

```text
Application Health != Git Synchronization State
```

### Evidence

```text
screenshots/phase-09-05-argocd-application-outofsync.png
```

---

## First GitOps Synchronization

The existing application resources were synchronized with the desired configuration managed through Argo CD.

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

This established Argo CD as the GitOps controller for the application.

### Evidence

```text
screenshots/phase-09-06-first-gitops-sync-success.png
```

---

## Automated Synchronization

Automated synchronization was configured using:

```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```

This changes the deployment model from manual synchronization toward continuous GitOps reconciliation.

The workflow becomes:

```text
Git Change
    |
    v
Argo CD Detects Difference
    |
    v
OutOfSync
    |
    v
Automatic Synchronization
    |
    v
Kubernetes Reconciliation
    |
    v
Synced + Healthy
```

---

## Automatic Pruning

Automatic pruning was enabled using:

```yaml
prune: true
```

With pruning enabled, resources removed from the Git-managed desired state can also be removed from Kubernetes during synchronization.

This helps prevent obsolete Git-managed resources from remaining in the cluster.

---

## Self-Healing

Self-healing was enabled using:

```yaml
selfHeal: true
```

This allows Argo CD to reconcile changes made directly to managed Kubernetes resources back toward the desired state stored in Git.

The control model becomes:

```text
Git
Desired State
     |
     v
Argo CD
Reconciliation Controller
     |
     v
Kubernetes
Actual State
```

---

## Server-Side Apply

The Application enables:

```yaml
syncOptions:
  - ServerSideApply=true
```

Server-Side Apply delegates field ownership management to the Kubernetes API server.

This is particularly relevant to this project because application resource management evolved through:

```text
kubectl
   |
   v
Helm
   |
   v
Argo CD
```

The option supports the transition toward declarative Argo CD management.

---

## Namespace Management

The following synchronization option was configured:

```yaml
syncOptions:
  - CreateNamespace=true
```

This allows Argo CD to ensure that the destination namespace exists when synchronization occurs.

The configured destination is:

```text
enterprise-devsecops
```

---

## Automated Sync Policy Verification

The synchronization policy was verified using:

```powershell
kubectl get application enterprise-devsecops `
  -n argocd `
  -o jsonpath="{.spec.syncPolicy}"
```

The configuration confirmed:

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

The Application reported:

```text
Sync Policy: Automated (Prune)
Sync Status: Synced
Health Status: Healthy
```

### Evidence

```text
screenshots/phase-09-07-argocd-automated-sync-enabled.png
screenshots/phase-09-07-argocd-synced-healthy-dashboard.png
```

---

## Git-Driven Deployment Test

To prove that Git was controlling the desired Kubernetes state, the Helm configuration was changed from:

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

The Application tracks:

```yaml
targetRevision: main
```

Therefore, the feature-branch change did not immediately affect the Kubernetes workload.

The desired workflow was:

```text
Feature Branch
      |
      v
replicaCount: 3
      |
      v
Commit
      |
      v
Pull Request
      |
      v
Repository Checks
      |
      v
Merge into main
      |
      v
Argo CD detects new revision
      |
      v
Automatic synchronization
      |
      v
Kubernetes reconciled
```

---

## Pull Request Validation

The GitOps implementation was submitted through a GitHub Pull Request.

Repository checks completed successfully before merge.

The Pull Request showed:

```text
All checks have passed
No conflicts with base branch
```

This ensured that the GitOps configuration followed the same controlled development workflow as the other project phases.

### Evidence

```text
screenshots/phase-09-08-github-pr-checks-passed.png
```

---

## Git-Driven Automatic Reconciliation

After the Pull Request was merged into `main`, Argo CD detected the new Git revision.

The desired Helm state was now:

```yaml
replicaCount: 3
```

Argo CD automatically reconciled the Kubernetes Deployment.

No manual deployment command was required after the Git change was merged.

The following were not required to deploy the replica change:

```text
kubectl apply
helm upgrade
argocd app sync
```

The Kubernetes Deployment reached:

```text
READY:       3/3
UP-TO-DATE:  3
AVAILABLE:   3
```

Three application Pods were running.

Argo CD reported:

```text
Sync Policy: Automated (Prune)
Sync Status: Synced
Health Status: Healthy
```

This validated the Git-driven continuous delivery workflow:

```text
Git Desired State
replicaCount: 3
        |
        v
Merge into main
        |
        v
Argo CD Detects Revision
        |
        v
Automatic Sync
        |
        v
Helm Rendering
        |
        v
Kubernetes Reconciliation
        |
        v
3 Running Replicas
        |
        v
Synced + Healthy
```

### Evidence

```text
screenshots/phase-09-09-git-driven-auto-sync.png
```

---

## Self-Healing Validation

After validating Git-driven synchronization, a controlled configuration drift was intentionally introduced.

The Git-defined desired state was:

```yaml
replicaCount: 3
```

The live Kubernetes Deployment was manually changed using:

```powershell
kubectl scale deployment/enterprise-devsecops-app `
  --replicas=5 `
  -n enterprise-devsecops
```

The intended drift was:

```text
Git Desired State:       3 replicas
Manual Kubernetes Scale: 5 replicas
```

Because Argo CD self-healing was enabled, the live configuration was automatically reconciled back toward the desired state stored in Git.

After reconciliation:

```powershell
kubectl get deployment enterprise-devsecops-app `
  -n enterprise-devsecops
```

showed:

```text
READY:       3/3
UP-TO-DATE:  3
AVAILABLE:   3
```

The application Pods were checked using:

```powershell
kubectl get pods -n enterprise-devsecops
```

Three running Pods remained.

The Argo CD Application reported:

```text
Sync Policy: Automated (Prune)
Sync Status: Synced
Health Status: Healthy
```

The reconciliation happened quickly enough that the requested five-replica state had already been corrected when the Deployment was subsequently inspected.

This validates configuration-drift correction:

```text
Git Desired State
3 Replicas
     |
     v
Manual Cluster Change
5 Replicas Requested
     |
     v
Configuration Drift
     |
     v
Argo CD Self-Healing
     |
     v
Kubernetes Reconciled
     |
     v
3 Replicas
     |
     v
Synced + Healthy
```

### Evidence

```text
screenshots/phase-09-10-argocd-self-healing-success.png
```

---

## Complete GitOps Workflow

The completed GitOps delivery workflow is:

```text
Developer
    |
    v
Feature Branch
    |
    v
Configuration Change
    |
    v
Git Commit
    |
    v
GitHub Pull Request
    |
    v
Repository / CI Checks
    |
    v
Merge into main
    |
    v
Argo CD
    |
    v
Helm Chart Rendering
    |
    v
Kubernetes Reconciliation
    |
    v
Application Deployment
    |
    v
Synced + Healthy
```

The drift-recovery workflow is:

```text
Git Desired State
        |
        v
Argo CD
        |
        v
Kubernetes
        |
   Manual Drift
        |
        v
Argo CD Detects Difference
        |
        v
Self-Healing
        |
        v
Desired State Restored
```

---

## Screenshots

Phase 9 evidence:

```text
phase-09-01-argocd-application-validation.png
phase-09-01-pre-gitops-cluster-state.png
phase-09-02-argocd-components-running.png
phase-09-03-argocd-dashboard.png
phase-09-04-argocd-cli-access.png
phase-09-05-argocd-application-outofsync.png
phase-09-06-first-gitops-sync-success.png
phase-09-07-argocd-automated-sync-enabled.png
phase-09-07-argocd-synced-healthy-dashboard.png
phase-09-08-github-pr-checks-passed.png
phase-09-09-git-driven-auto-sync.png
phase-09-10-argocd-self-healing-success.png
```

These screenshots provide evidence for:

- Pre-GitOps Kubernetes state
- Argo CD Application validation
- Argo CD components
- Dashboard access
- CLI authentication
- Initial OutOfSync detection
- First synchronization
- Automated synchronization
- Synced and Healthy dashboard state
- GitHub Pull Request checks
- Git-driven automatic deployment
- Self-healing and drift correction

---

## Key Technical Learnings

### Git Is the Desired-State Source

The deployment model now follows:

```text
Git = Desired State
Kubernetes = Actual State
Argo CD = Reconciliation Controller
```

Changes intended for the application should flow through Git rather than being applied directly to the cluster.

### Health and Synchronization Are Separate

The project observed:

```text
Healthy + OutOfSync
```

The application could remain operational while its Kubernetes configuration differed from Git.

After reconciliation:

```text
Healthy + Synced
```

confirmed both workload health and desired-state alignment.

### Feature Branches Do Not Automatically Become Desired State

Because the Application tracks:

```yaml
targetRevision: main
```

a change on:

```text
feature/argocd-gitops
```

did not affect the workload until it was merged into `main`.

This establishes the controlled deployment path:

```text
Feature Branch
      |
      v
Pull Request
      |
      v
Checks
      |
      v
Merge
      |
      v
main
      |
      v
Argo CD
```

### Automated Sync Enables Git-Driven Deployment

After the replica change was merged, no manual deployment command was required.

Argo CD automatically detected the Git change and reconciled Kubernetes from two to three replicas.

### Self-Healing Corrects Configuration Drift

A manual attempt to scale the live Deployment to five replicas was automatically reconciled back to the Git-defined three replicas.

This demonstrates continuous desired-state enforcement.

### Helm and Argo CD Have Different Responsibilities

Helm provides:

```text
Packaging
Templating
Configurable Kubernetes manifests
```

Argo CD provides:

```text
Git monitoring
Desired-state comparison
Automatic synchronization
Pruning
Drift detection
Self-healing
Continuous delivery
```

Together:

```text
Git
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

### Server-Side Apply Supports Declarative Resource Management

The project uses:

```yaml
ServerSideApply=true
```

The application's management lifecycle evolved through:

```text
kubectl
   |
   v
Helm
   |
   v
Argo CD
```

This demonstrates the migration of an existing Kubernetes workload toward declarative GitOps management.

---

## Phase 9 Final Outcome

Phase 9 successfully implemented GitOps continuous delivery for the Enterprise DevSecOps Platform.

Completed capabilities:

- Argo CD installed on Kubernetes
- Argo CD components validated
- Argo CD dashboard accessed
- Argo CD CLI installed
- CLI authentication verified
- Kubernetes connectivity verified
- Declarative Argo CD Application created
- GitHub configured as the desired-state source
- Helm chart integrated with Argo CD
- Application manifest validated
- Initial OutOfSync state observed
- First GitOps synchronization completed
- Application reached Synced and Healthy
- Automated synchronization enabled
- Automatic pruning enabled
- Self-healing enabled
- Server-Side Apply enabled
- Namespace creation option enabled
- Git-driven replica change implemented
- Pull Request checks completed successfully
- Configuration merged into `main`
- Argo CD detected the new Git revision
- Deployment automatically scaled from two to three replicas
- Manual Kubernetes drift introduced
- Argo CD automatically corrected the drift
- Deployment returned to the Git-defined three replicas
- Final Application state verified as Synced and Healthy

---

## Phase 9 Status

```text
ARGO CD GITOPS CONTINUOUS DELIVERY: COMPLETE
```

The Enterprise DevSecOps Platform now supports a Git-driven continuous delivery workflow where application configuration is promoted through Git and automatically reconciled into Kubernetes through Argo CD.

Final deployment path:

```text
Code / Configuration
        |
        v
Feature Branch
        |
        v
Pull Request
        |
        v
Repository Checks
        |
        v
Merge into main
        |
        v
Argo CD
        |
        v
Helm
        |
        v
Kubernetes
        |
        v
Application
```

Final reconciliation model:

```text
                 Git
           Desired State
                 |
                 v
              Argo CD
             /       \
            v         v
       Auto Sync   Self-Healing
            \         /
             \       /
                 v
             Kubernetes
                 |
                 v
          Synced + Healthy
```

Phase 9 is complete.