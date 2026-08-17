# Phase 8 — Helm Packaging and Release Management

## Objective

Convert the Kubernetes manifests created during Phase 7 into a reusable Helm chart and introduce structured Kubernetes application release management.

This phase focuses on:

- Helm chart creation
- Kubernetes manifest templating
- Centralized configuration using `values.yaml`
- Reusable Deployment and Service templates
- Helm linting and template validation
- Server-side dry-run validation
- Migration of existing Kubernetes resources into Helm management
- Kubernetes field ownership troubleshooting
- Helm release upgrades
- Runtime value overrides
- Helm revision history
- Helm rollback
- Post-rollback health validation
- Helm chart packaging

The goal is to move from individually managed Kubernetes YAML files toward a repeatable and versioned application deployment model.

---

# 1. Starting Point

Phase 7 deployed the Enterprise DevSecOps Platform directly using Kubernetes manifests:

```text
kubernetes/
├── namespace.yaml
├── deployment.yaml
└── service.yaml
```

Resources were applied using:

```powershell
kubectl apply -f kubernetes\namespace.yaml
kubectl apply -f kubernetes\deployment.yaml
kubectl apply -f kubernetes\service.yaml
```

The application was successfully running with:

```text
Namespace
    ↓
Deployment
    ↓
ReplicaSet
    ↓
2 Application Pods
    ↓
ClusterIP Service
```

Phase 8 introduces Helm on top of this working Kubernetes environment.

---

# 2. Helm Environment

Helm was installed and validated using:

```powershell
helm version
```

Environment used during this phase:

```text
Helm:        v4.2.4
Kubernetes:  v1.36.1
kubectl:     v1.36.1
Cluster:     Docker Desktop Kubernetes
Context:     docker-desktop
```

The Kubernetes cluster was verified before beginning the Helm migration:

```powershell
kubectl config current-context
kubectl get nodes
kubectl get all -n enterprise-devsecops
```

This ensured that Helm packaging work started from a healthy Kubernetes workload.

---

# 3. Helm Chart Creation

The Helm chart was created inside the existing `helm` directory:

```powershell
helm create helm\enterprise-devsecops
```

Initial chart structure:

```text
helm/
└── enterprise-devsecops/
    ├── charts/
    ├── templates/
    ├── .helmignore
    ├── Chart.yaml
    └── values.yaml
```

The default Helm-generated templates were reviewed.

Templates not required for this phase were removed and replaced with project-specific resources.

The final chart focuses on:

```text
Namespace
Deployment
Service
```

---

# 4. Chart Metadata

The chart metadata is defined in:

```text
helm/enterprise-devsecops/Chart.yaml
```

Configuration:

```yaml
apiVersion: v2

name: enterprise-devsecops

description: Helm chart for the Enterprise DevSecOps Platform

type: application

version: 0.1.0

appVersion: "1.0.1"
```

The chart version and application version are intentionally maintained separately.

```text
Chart Version
0.1.0

Application Version
1.0.1
```

This allows the Helm packaging lifecycle to evolve independently from the containerized application version.

---

# 5. Centralized Helm Values

Application deployment configuration was moved into:

```text
helm/enterprise-devsecops/values.yaml
```

The chart uses centralized values for:

```text
Replica count
Namespace
Container image
Image tag
Image pull policy
Container port
Service configuration
Liveness probe
Readiness probe
CPU requests
Memory requests
CPU limits
Memory limits
Container security context
```

Key configuration:

```yaml
replicaCount: 2

namespace:
  create: true
  name: enterprise-devsecops

image:
  repository: enterprise-devsecops-platform
  tag: "1.0.1"
  pullPolicy: IfNotPresent

container:
  port: 5000

service:
  type: ClusterIP
  port: 80
```

Resource configuration:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"

  limits:
    cpu: "500m"
    memory: "256Mi"
```

Container security configuration:

```yaml
securityContext:
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  runAsUser: 100
  runAsGroup: 101
  dropCapabilities:
    - ALL
```

Centralizing these settings makes the chart easier to reuse across different environments.

---

# 6. Health Probe Configuration

The application retains the health checks introduced during Phase 7.

Liveness configuration:

```yaml
probes:
  liveness:
    path: /health
    initialDelaySeconds: 10
    periodSeconds: 10
    timeoutSeconds: 3
    failureThreshold: 3
```

Readiness configuration:

```yaml
probes:
  readiness:
    path: /ready
    initialDelaySeconds: 5
    periodSeconds: 5
    timeoutSeconds: 3
    failureThreshold: 3
```

These checks allow Kubernetes to distinguish between:

```text
Container process running
        ↓
Application healthy
        ↓
Application ready to receive traffic
```

---

# 7. Helm Templates

Project-specific templates were created under:

```text
helm/enterprise-devsecops/templates/
```

The chart contains reusable templates for:

```text
namespace.yaml
deployment.yaml
service.yaml
_helpers.tpl
NOTES.txt
```

The Deployment template dynamically consumes values from `values.yaml`.

Conceptually:

```text
values.yaml
      ↓
Helm Template Engine
      ↓
deployment.yaml
service.yaml
namespace.yaml
      ↓
Rendered Kubernetes Resources
```

---

# 8. Helm Helper Templates

Reusable chart metadata and labels are maintained through:

```text
_templates/_helpers.tpl
```

The helper logic was simplified during the Kubernetes-to-Helm migration so that Helm preserved the existing workload identity.

The stable selector helper became:

```tpl
{{- define "enterprise-devsecops.selectorLabels" -}}
app: enterprise-devsecops-app
{{- end }}
```

This became important when adopting resources originally created using `kubectl`.

---

# 9. Helm Chart Validation

Before interacting with the Kubernetes API server, the chart was validated locally.

Command:

```powershell
helm lint helm\enterprise-devsecops
```

Result:

```text
1 chart(s) linted, 0 chart(s) failed
```

Helm also reported:

```text
[INFO] Chart.yaml: icon is recommended
```

This is informational and does not represent a chart validation failure.

The lint result confirmed that the chart structure and templates were valid.

---

# 10. Local Template Rendering

The chart was rendered locally using:

```powershell
helm template enterprise-devsecops `
  helm\enterprise-devsecops
```

The rendered output contained:

```text
Namespace
Service
Deployment
```

This allowed the generated Kubernetes manifests to be inspected before modifying the cluster.

Important properties verified included:

```text
Resource names
Namespace
Container image
Replica count
Service port
Container port
Liveness probe
Readiness probe
Resource limits
Security context
Deployment selector
Service selector
```

---

# 11. Existing Resource Adoption Challenge

The Kubernetes resources created during Phase 7 already existed before Helm was introduced.

These resources were originally created using:

```powershell
kubectl apply
```

Existing resources included:

```text
Namespace
Deployment
Service
```

When Helm was introduced during Phase 8, the chart attempted to manage resources with the same names.

The initial adoption attempt used:

```powershell
helm install enterprise-devsecops `
  helm\enterprise-devsecops `
  --namespace enterprise-devsecops `
  --take-ownership `
  --wait
```

The installation encountered Kubernetes field ownership conflicts.

The conflicts were associated with:

```text
kubectl-client-side-apply
```

and affected fields in the existing Service and Deployment.

Examples included:

```text
Service
- metadata labels
- selector fields

Deployment
- metadata labels
- selector fields
- Pod template labels
```

This became an important troubleshooting scenario because Helm release ownership and Kubernetes field ownership are related but different concepts.

---

# 12. Helm Ownership vs Kubernetes Field Ownership

The migration demonstrated the difference between:

```text
Helm Release Ownership
```

and:

```text
Kubernetes Field Ownership
```

`--take-ownership` allows Helm to adopt resources that were not originally created by the release.

However, Kubernetes can still track individual fields as being managed by another field manager.

In this case:

```text
kubectl-client-side-apply
```

still had ownership relationships with fields in the live resources.

Therefore, successful migration required the Helm-rendered resources to remain compatible with the existing Kubernetes configuration.

---

# 13. Selector Compatibility Investigation

The original Phase 7 Deployment used the selector:

```yaml
selector:
  matchLabels:
    app: enterprise-devsecops-app
```

The initial Helm-generated templates introduced additional selector labels.

For example:

```yaml
app.kubernetes.io/name: enterprise-devsecops
app.kubernetes.io/instance: enterprise-devsecops
```

Changing the workload identity during migration was unnecessary and could introduce deployment compatibility problems.

The chart was therefore changed to preserve the original selector.

Final Deployment selector:

```yaml
selector:
  matchLabels:
    app: enterprise-devsecops-app
```

Final Service selector:

```yaml
selector:
  app: enterprise-devsecops-app
```

This preserved compatibility with the Phase 7 workload.

---

# 14. Helm Metadata Without Changing Workload Identity

Helm-specific management labels were retained on resource metadata:

```yaml
app.kubernetes.io/managed-by: Helm
helm.sh/chart: enterprise-devsecops-0.1.0
```

At the same time, the workload selector remained:

```yaml
app: enterprise-devsecops-app
```

This created a clean separation between:

```text
Application identity
```

and:

```text
Helm management metadata
```

The migration therefore did not require changing the existing application identity.

---

# 15. Layered Migration Validation

Rather than forcing changes directly onto the healthy Kubernetes workload, the migration was validated progressively.

The strategy became:

```text
Existing Kubernetes Resources
        ↓
Helm Lint
        ↓
Local Template Rendering
        ↓
Compare Existing and Rendered Resources
        ↓
Preserve Stable Selectors
        ↓
Server-Side Dry Run
        ↓
Controlled Helm Adoption
```

This reduced the risk of breaking the running application.

---

# 16. Server-Side Helm Upgrade Dry Run

Because the initial adoption attempt had already created Helm release history, the corrected migration used:

```powershell
helm upgrade
```

instead of repeating `helm install`.

The corrected chart was validated against the live Kubernetes API server using:

```powershell
helm upgrade enterprise-devsecops `
  helm\enterprise-devsecops `
  --namespace enterprise-devsecops `
  --take-ownership `
  --dry-run=server `
  --debug
```

The server-side validation completed successfully.

Example result:

```text
STATUS: pending-upgrade
DESCRIPTION: Dry run complete
```

A later final validation produced:

```text
REVISION: 5
STATUS: pending-upgrade
DESCRIPTION: Dry run complete
```

Because this was a dry run, it did not replace the currently deployed release revision.

---

# 17. Successful Helm Resource Adoption

After the corrected templates passed server-side validation, the real Helm migration was performed.

Command:

```powershell
helm upgrade enterprise-devsecops `
  helm\enterprise-devsecops `
  --namespace enterprise-devsecops `
  --take-ownership `
  --wait `
  --timeout 2m
```

The migration completed successfully and the release reached:

```text
STATUS: deployed
```

The Kubernetes application remained healthy after adoption.

The transition was:

```text
kubectl-managed resources
        ↓
Helm template alignment
        ↓
Server-side validation
        ↓
Helm resource adoption
        ↓
Helm-managed release
```

---

# 18. Helm Release Verification

The release was verified using:

```powershell
helm list -n enterprise-devsecops
```

and:

```powershell
helm status enterprise-devsecops `
  -n enterprise-devsecops
```

The successful release reported:

```text
STATUS: deployed
```

The Deployment and Service also contained Helm management metadata.

This confirmed that the application had transitioned into Helm release management.

---

# 19. Application Health Validation After Adoption

The application was accessed using Kubernetes port forwarding:

```powershell
kubectl port-forward `
  service/enterprise-devsecops-service `
  8080:80 `
  -n enterprise-devsecops
```

Health endpoint:

```powershell
Invoke-RestMethod http://localhost:8080/health
```

Result:

```text
service                       status
-------                       ------
enterprise-devsecops-platform healthy
```

Readiness endpoint:

```powershell
Invoke-RestMethod http://localhost:8080/ready
```

Result:

```text
service                       status
-------                       ------
enterprise-devsecops-platform ready
```

This confirmed that the migration to Helm management did not break application availability.

---

# 20. Helm Upgrade Validation

After successful Helm adoption, release upgrade behavior was tested.

The application was temporarily scaled from two replicas to three using a Helm value override:

```powershell
helm upgrade enterprise-devsecops `
  helm\enterprise-devsecops `
  --namespace enterprise-devsecops `
  --set replicaCount=3 `
  --wait `
  --timeout 2m
```

The command completed successfully:

```text
STATUS: deployed
REVISION: 3
DESCRIPTION: Upgrade complete
```

The Deployment was verified:

```powershell
kubectl get deployment enterprise-devsecops-app `
  -n enterprise-devsecops
```

Result:

```text
READY       3/3
UP-TO-DATE  3
AVAILABLE   3
```

Three application Pods were running successfully.

---

# 21. Runtime Value Override

The default chart configuration remained:

```yaml
replicaCount: 2
```

During the upgrade, this was overridden with:

```powershell
--set replicaCount=3
```

The effective release configuration was verified using:

```powershell
helm get values enterprise-devsecops `
  -n enterprise-devsecops
```

Result:

```yaml
replicaCount: 3
```

This demonstrates an important Helm capability:

```text
Chart Default
replicaCount: 2

        +

Runtime Override
--set replicaCount=3

        ↓

Rendered Deployment
replicas: 3
```

No permanent modification of `values.yaml` was required for this test.

---

# 22. Helm Release History

Release history was inspected using:

```powershell
helm history enterprise-devsecops `
  -n enterprise-devsecops
```

The lifecycle showed:

```text
Revision 1
Initial adoption attempt

Revision 2
Successful Helm adoption

Revision 3
Upgrade to three replicas
```

After rollback, the history became:

```text
Revision 1  → superseded
Revision 2  → superseded
Revision 3  → superseded
Revision 4  → deployed
```

Revision 4 represented:

```text
Rollback to 2
```

This demonstrates that Helm maintains release history instead of replacing previous release state.

---

# 23. Helm Rollback Validation

The three-replica upgrade was intentionally rolled back to the previous stable configuration.

Command:

```powershell
helm rollback enterprise-devsecops 2 `
  -n enterprise-devsecops `
  --wait
```

Result:

```text
Rollback was a success! Happy Helming!
```

The Deployment was verified again:

```powershell
kubectl get deployment enterprise-devsecops-app `
  -n enterprise-devsecops
```

Result:

```text
READY       2/2
UP-TO-DATE  2
AVAILABLE   2
```

The temporary third Pod was terminated and the application returned to its stable two-replica configuration.

---

# 24. Rollback Revision Behavior

The rollback did not delete the previous upgrade revision.

Instead, Helm created a new release revision.

The release lifecycle became:

```text
Revision 1
Initial adoption attempt
        ↓
Revision 2
Successful adoption
        ↓
Revision 3
Upgrade to 3 replicas
        ↓
Revision 4
Rollback to revision 2
        ↓
2-replica stable configuration
```

This provides a traceable deployment history and allows previous release states to be investigated.

---

# 25. Post-Rollback Application Validation

After rollback, application health was tested again.

Port forwarding:

```powershell
kubectl port-forward `
  service/enterprise-devsecops-service `
  8080:80 `
  -n enterprise-devsecops
```

Health validation:

```powershell
Invoke-RestMethod http://localhost:8080/health
```

Result:

```text
enterprise-devsecops-platform healthy
```

Readiness validation:

```powershell
Invoke-RestMethod http://localhost:8080/ready
```

Result:

```text
enterprise-devsecops-platform ready
```

This confirmed that the rollback restored a functional and healthy application release.

---

# 26. Helm Chart Packaging

After validating installation, upgrades, and rollback behavior, the chart was packaged for distribution.

Package directory:

```powershell
New-Item -ItemType Directory `
  -Path helm\packages `
  -Force
```

Chart packaging:

```powershell
helm package helm\enterprise-devsecops `
  --destination helm\packages
```

Result:

```text
Successfully packaged chart and saved it to:
helm\packages\enterprise-devsecops-0.1.0.tgz
```

Generated package:

```text
helm/packages/enterprise-devsecops-0.1.0.tgz
```

---

# 27. Packaged Chart Validation

The packaged chart metadata was inspected using:

```powershell
helm show chart `
  helm\packages\enterprise-devsecops-0.1.0.tgz
```

Validated metadata:

```text
apiVersion: v2
name: enterprise-devsecops
type: application
version: 0.1.0
appVersion: 1.0.1
```

The packaged default values were also inspected:

```powershell
helm show values `
  helm\packages\enterprise-devsecops-0.1.0.tgz
```

The package retained the expected default configuration:

```text
replicaCount: 2

image:
  repository: enterprise-devsecops-platform
  tag: 1.0.1

service:
  type: ClusterIP
  port: 80
```

The packaged artifact can now be versioned and distributed independently from the source chart directory.

---

# 28. Final Runtime Validation

After the upgrade and rollback tests, the final release was checked using:

```powershell
helm list -n enterprise-devsecops
```

Final Helm state:

```text
RELEASE:     enterprise-devsecops
REVISION:    4
STATUS:      deployed
CHART:       enterprise-devsecops-0.1.0
APP VERSION: 1.0.1
```

Release history:

```text
Revision 1 → superseded
Revision 2 → superseded
Revision 3 → superseded
Revision 4 → deployed — Rollback to 2
```

The Kubernetes environment was verified using:

```powershell
kubectl get all -n enterprise-devsecops
```

Final application state:

```text
Pods:        2 Running
Deployment:  2/2 Ready
Service:     ClusterIP
ReplicaSet:  2 desired / 2 current / 2 ready
```

This represents the final stable state of Phase 8.

---

# 29. Troubleshooting Summary

Phase 8 included a realistic migration challenge rather than only a clean Helm installation.

The troubleshooting sequence was:

```text
Existing kubectl-managed resources
        ↓
Initial Helm adoption attempt
        ↓
Field ownership conflict
        ↓
Inspect Kubernetes selectors
        ↓
Compare Helm-rendered resources
        ↓
Identify selector differences
        ↓
Preserve existing workload identity
        ↓
Simplify Helm selector helpers
        ↓
helm lint
        ↓
helm template
        ↓
Server-side dry run
        ↓
Successful Helm adoption
```

The key lesson was:

> Existing Kubernetes workloads should be migrated into Helm carefully rather than forcing a new chart structure onto healthy resources.

The migration preserved the stable resource identity while adding Helm release-management capabilities.

---

# 30. Engineering Decisions

## Why preserve the original selector?

Deployment selectors represent workload identity and should remain stable during migration.

The existing selector:

```yaml
app: enterprise-devsecops-app
```

already worked correctly.

Changing it simply to match Helm's default generated labels would add unnecessary migration risk.

---

## Why use `values.yaml`?

Hard-coded deployment configuration makes environment-specific deployments difficult.

Centralized values allow configuration to change without rewriting templates.

For example:

```powershell
helm upgrade enterprise-devsecops `
  helm\enterprise-devsecops `
  --set replicaCount=3
```

changed runtime capacity without editing the Deployment template.

---

## Why test rollback?

A deployment strategy should include recovery, not only deployment.

The rollback test demonstrated:

```text
Upgrade
   ↓
New Revision
   ↓
Validation
   ↓
Rollback
   ↓
Stable Previous Configuration
```

---

## Why package the chart?

The source chart is useful for development.

The `.tgz` artifact provides a versioned distributable package:

```text
enterprise-devsecops-0.1.0.tgz
```

This prepares the project for later artifact publishing and automated deployment workflows.

---

# 31. Screenshots / Evidence

Phase 8 evidence is stored under:

```text
screenshots/
```

Evidence captured:

```text
phase-08-01-helm-chart-created.png
phase-08-02-helm-chart-lint-success.png
phase-08-03-helm-dry-run-success.png
phase-08-04-helm-adoption-conflict.png
phase-08-05-helm-upgrade-dry-run-success.png
phase-08-06-helm-release-deployed.png
phase-08-07-helm-application-health.png
phase-08-08-helm-release-history.png
phase-08-09-helm-upgrade-three-replicas.png
phase-08-10-helm-upgrade-history.png
phase-08-11-helm-rollback-success.png
phase-08-12-helm-rollback-history.png
phase-08-13-helm-chart-packaged.png
```

These screenshots document both successful implementation and troubleshooting encountered during the phase.

---

# 32. Phase 8 Capabilities

Phase 8 introduced the following capabilities:

- Helm installation and validation
- Helm chart creation
- Custom `Chart.yaml`
- Centralized `values.yaml`
- Namespace templating
- Deployment templating
- Service templating
- Reusable helper templates
- Health probe configuration
- Resource requests and limits
- Non-root container configuration
- Linux capability dropping
- Helm lint validation
- Local Helm template rendering
- Kubernetes API server dry-run validation
- Existing Kubernetes resource migration
- Helm resource adoption
- Kubernetes field ownership troubleshooting
- Stable selector preservation
- Helm-managed release lifecycle
- Runtime configuration overrides
- Application scaling through Helm
- Helm revision history
- Helm rollback
- Post-rollback application verification
- Helm chart packaging
- Packaged chart inspection

---

# 33. Release Lifecycle Demonstrated

The complete Phase 8 lifecycle was:

```text
Phase 7 Kubernetes Deployment
            ↓
Existing kubectl-managed Resources
            ↓
Create Helm Chart
            ↓
Configure values.yaml
            ↓
Build Kubernetes Templates
            ↓
helm lint
            ↓
helm template
            ↓
Initial Adoption Attempt
            ↓
Field Ownership Conflict
            ↓
Selector Investigation
            ↓
Template Alignment
            ↓
Server-Side Dry Run
            ↓
Successful Helm Adoption
            ↓
Release Revision 2
            ↓
Helm Upgrade
            ↓
3 Replicas
            ↓
Release Revision 3
            ↓
Helm Rollback
            ↓
Release Revision 4
            ↓
2 Replicas Restored
            ↓
Application Health Validation
            ↓
Package Helm Chart
            ↓
enterprise-devsecops-0.1.0.tgz
```

---

# 34. Key Learning

This phase demonstrated that Helm is more than a YAML templating tool.

It provides a structured release-management layer around Kubernetes applications.

The most important lessons from this phase were:

1. Existing Kubernetes resources require careful migration into Helm.
2. Helm ownership and Kubernetes field ownership are not identical.
3. Stable Deployment selectors should be preserved during migration.
4. `helm lint` validates chart structure before deployment.
5. `helm template` allows generated resources to be inspected locally.
6. Server-side dry runs reduce migration risk.
7. `values.yaml` separates configuration from resource templates.
8. Runtime values can override chart defaults.
9. Helm maintains revision history across upgrades.
10. Rollback creates a new release revision rather than deleting history.
11. Application health must be verified after both upgrades and rollbacks.
12. Packaged charts provide versioned deployment artifacts.

---

# 35. Phase 8 Final Outcome

Phase 8 successfully transformed the Enterprise DevSecOps Platform from:

```text
Static Kubernetes Manifests
```

into:

```text
Reusable Helm Chart
        +
Centralized Configuration
        +
Release Management
        +
Upgrade Capability
        +
Rollback Capability
        +
Packaged Deployment Artifact
```

Final release state:

```text
Helm Release:     enterprise-devsecops
Chart Version:    0.1.0
Application:      1.0.1
Current Revision: 4
Status:           deployed
Replicas:         2/2
Application:      healthy and ready
```

Final package:

```text
helm/packages/enterprise-devsecops-0.1.0.tgz
```

---

# Phase 8 Status

```text
HELM PACKAGING AND RELEASE MANAGEMENT: COMPLETE
```

Next:

```text
Final Git Validation
        ↓
Commit
        ↓
Push Feature Branch
        ↓
Pull Request
        ↓
CI / Security Checks
        ↓
Merge into main
```