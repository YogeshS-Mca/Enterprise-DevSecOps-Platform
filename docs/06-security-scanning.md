# Phase 6 — DevSecOps Security Scanning

## Objective

Integrate security scanning into the Enterprise DevSecOps Platform using Trivy and GitHub Actions.

The objective of this phase is to introduce security checks earlier in the development lifecycle so that vulnerabilities, secrets, and misconfigurations can be detected before code is merged into the main branch.

This follows the DevSecOps principle of **shift-left security**.

---

## Tools Used

* Trivy
* Docker
* Git
* GitHub Actions
* PowerShell
* Pytest

---

## Security Workflow Overview

The security process implemented in this phase follows this flow:

```text
Developer Changes
        ↓
Local Testing
        ↓
Docker Image Build
        ↓
Repository Security Scan
        ↓
Container Image Scan
        ↓
Vulnerability Analysis
        ↓
Runtime Verification
        ↓
GitHub Actions Security Workflow
        ↓
Pull Request Review
        ↓
Merge
```

---

# 1. Repository Security Scan

The first security activity was scanning the complete project repository using Trivy.

The scan checks the repository for:

* Dependency vulnerabilities
* Secrets
* Misconfigurations
* Security issues in configuration files

The repository was mounted inside a Trivy container and scanned.

Example command:

```powershell
docker run --rm `
  --network host `
  -v "${PWD}:/project" `
  aquasec/trivy:latest `
  repo /project
```

---

## Initial Repository Scan Issue

The first repository scan failed with a timeout.

### Error

```text
context deadline exceeded
```

The scan was spending a large amount of time analyzing files inside the local Python virtual environment.

The affected directory was:

```text
.venv/
```

The `.venv` directory contains a large number of installed Python packages, compiled files, cache files, and development dependencies.

These files are not part of the source code that should be committed to Git.

---

## Root Cause

Trivy recursively traversed the local Python virtual environment.

The large number of files inside `.venv` caused repository traversal to exceed the default scan timeout.

---

## Resolution

The local virtual environment was excluded from the repository scan using:

```text
--skip-dirs /project/.venv
```

The scan timeout was also increased:

```text
--timeout 10m
```

The corrected command was:

```powershell
docker run --rm `
  --network host `
  -v "${PWD}:/project" `
  aquasec/trivy:latest `
  repo `
  --skip-dirs /project/.venv `
  --timeout 10m `
  /project
```

This allowed the repository scan to complete successfully.

---

# 2. Repository Security Report

A JSON security report was generated for traceability and documentation.

Command:

```powershell
docker run --rm `
  --network host `
  -v "${PWD}:/project" `
  aquasec/trivy:latest `
  repo `
  --skip-dirs /project/.venv `
  --timeout 10m `
  --format json `
  --output /project/security/reports/trivy-repository-report.json `
  /project
```

Generated file:

```text
security/reports/trivy-repository-report.json
```

This report can be used for:

* Security review
* Historical comparison
* Audit evidence
* Vulnerability analysis

---

# 3. Container Image Security Scan

The Docker image was scanned using Trivy.

Image scanned:

```text
enterprise-devsecops-platform:ci
```

Command:

```powershell
docker run --rm `
  --network host `
  -v /var/run/docker.sock:/var/run/docker.sock `
  aquasec/trivy:latest `
  image `
  --severity HIGH,CRITICAL `
  enterprise-devsecops-platform:ci
```

---

## Initial Image Scan Result

The initial container scan detected HIGH and CRITICAL vulnerabilities.

The findings were separated into:

```text
Operating System vulnerabilities
Python package vulnerabilities
```

The Debian base-image scan initially reported:

```text
HIGH: 19
CRITICAL: 4
```

The Python package scan reported:

```text
HIGH: 2
CRITICAL: 0
```

---

# 4. Actionable Vulnerability Analysis

Not every vulnerability reported by a scanner can be fixed immediately.

Some vulnerabilities may not yet have a vendor-provided patch.

To separate actionable findings from vulnerabilities without available fixes, the following option was used:

```text
--ignore-unfixed
```

Command:

```powershell
docker run --rm `
  --network host `
  -v /var/run/docker.sock:/var/run/docker.sock `
  aquasec/trivy:latest `
  image `
  --ignore-unfixed `
  --severity HIGH,CRITICAL `
  enterprise-devsecops-platform:ci
```

---

## Result After Filtering Unfixed Vulnerabilities

After filtering vulnerabilities without available fixes:

```text
Debian OS:
0 actionable HIGH/CRITICAL vulnerabilities
```

Python findings remained:

```text
HIGH: 2
CRITICAL: 0
```

This demonstrated that the previously reported Debian vulnerabilities did not currently have vendor fixes available.

---

# 5. Python Vulnerability Findings

Trivy reported two HIGH-severity Python findings:

```text
msgpack 1.1.2
setuptools 70.3.0
```

Reported remediation versions:

```text
msgpack:
1.1.2 → 1.2.1

setuptools:
70.3.0 → 78.1.1
```

Instead of immediately modifying application dependencies, the findings were verified inside the actual runtime container.

---

# 6. Runtime Verification of Python Findings

The following command was used to check `msgpack`:

```powershell
docker run --rm `
  --entrypoint python `
  enterprise-devsecops-platform:security `
  -m pip show msgpack
```

Result:

```text
Package(s) not found: msgpack
```

The following command was used to check `setuptools`:

```powershell
docker run --rm `
  --entrypoint python `
  enterprise-devsecops-platform:security `
  -m pip show setuptools
```

Result:

```text
Package(s) not found: setuptools
```

---

## Runtime Package Verification

The complete runtime Python package list was checked using:

```powershell
docker run --rm `
  --entrypoint python `
  enterprise-devsecops-platform:security `
  -m pip list
```

The actual runtime environment contained:

```text
blinker
click
Flask
itsdangerous
Jinja2
MarkupSafe
pip
prometheus-client
waitress
Werkzeug
```

Neither `msgpack` nor `setuptools` was present in the runtime Python environment.

---

# 7. Precise Library Scan

To further investigate the Python findings, Trivy was executed using a more precise package-detection mode.

Command:

```powershell
docker run --rm `
  --network host `
  -v /var/run/docker.sock:/var/run/docker.sock `
  aquasec/trivy:latest `
  image `
  --pkg-types library `
  --detection-priority precise `
  --ignore-unfixed `
  --severity HIGH,CRITICAL `
  enterprise-devsecops-platform:security
```

The same two Python findings remained.

Trivy also displayed a warning related to third-party SBOM information.

---

## Security Decision

No unnecessary packages were added to the application merely to remove scanner findings.

The runtime container was directly inspected and confirmed that:

```text
msgpack is not installed
setuptools is not installed
```

Therefore, the findings were documented for traceability rather than changing the application's actual dependency set.

This prevents introducing unnecessary packages into the production image.

---

# 8. Security Image Build

A dedicated security-validation Docker image was created:

```text
enterprise-devsecops-platform:security
```

Local build command:

```powershell
docker build `
  --network=host `
  -t enterprise-devsecops-platform:security .
```

The `--network=host` option was required on the local Windows environment because Docker bridge networking had previously experienced outbound HTTPS connectivity problems.

This option is used only during local build-time dependency installation.

---

# 9. Application Regression Testing

Security changes should never break application functionality.

After completing the security analysis, the existing test suite was executed again.

Command:

```powershell
python -m pytest -v
```

Result:

```text
5 passed
```

The following endpoints remained validated:

* `/`
* `/health`
* `/ready`
* `/metrics`
* Unknown endpoint / 404 behavior

This confirmed that the security work did not introduce application regressions.

---

# 10. Security Reports

The following security reports were generated:

```text
security/reports/trivy-repository-report.json
security/reports/trivy-image-report.json
```

These files provide machine-readable security evidence and can be used for future comparison and auditing.

---

# 11. GitHub Actions Security Workflow

A GitHub Actions security workflow was added at:

```text
.github/workflows/security.yml
```

The workflow performs:

1. Repository checkout
2. Repository security scanning
3. Vulnerability scanning
4. Secret scanning
5. Misconfiguration scanning
6. Docker image build
7. Container image vulnerability scanning

---

## Security Workflow Configuration

The repository scan uses:

```yaml
scan-type: fs
scan-ref: .
scanners: vuln,secret,misconfig
severity: HIGH,CRITICAL
ignore-unfixed: true
exit-code: 0
```

The container image scan uses:

```yaml
image-ref: enterprise-devsecops-platform:security
severity: HIGH,CRITICAL
ignore-unfixed: true
exit-code: 0
```

---

# 12. Why `exit-code: 0` Is Used

The first version of the security pipeline establishes a security baseline.

Using:

```text
exit-code: 0
```

means:

```text
Security finding detected
        ↓
Finding is reported
        ↓
Workflow continues
        ↓
Developer reviews result
```

The pipeline currently observes and reports vulnerabilities without automatically blocking pull requests.

---

# 13. Future Security Gate

After the security baseline is stable and actionable findings are understood, selected scans can use:

```text
exit-code: 1
```

This changes the workflow to:

```text
HIGH / CRITICAL actionable vulnerability
        ↓
Security scan fails
        ↓
GitHub Actions job fails
        ↓
Pull request is blocked
        ↓
Developer must remediate or document risk
```

This creates a true security quality gate.

---

# 14. Shift-Left Security

This phase implements the DevSecOps concept of shift-left security.

Traditional approach:

```text
Develop
→ Build
→ Deploy
→ Discover security issue
```

Shift-left approach:

```text
Develop
→ Test
→ Scan
→ Review
→ Build
→ Deploy
```

Security issues are identified earlier, when they are generally easier and safer to investigate.

---

# 15. Troubleshooting Summary

Several real-world issues were encountered during this phase.

## Repository Scan Timeout

### Problem

```text
context deadline exceeded
```

### Root Cause

Trivy recursively scanned `.venv`.

### Resolution

```text
--skip-dirs /project/.venv
--timeout 10m
```

---

## Large Number of OS Vulnerabilities

### Problem

The initial Debian image scan reported multiple HIGH and CRITICAL vulnerabilities.

### Investigation

The scan was repeated using:

```text
--ignore-unfixed
```

### Result

No actionable Debian HIGH/CRITICAL vulnerabilities remained.

---

## Python Findings

### Problem

Trivy reported vulnerabilities for:

```text
msgpack
setuptools
```

### Investigation

The runtime image was directly inspected using:

```text
pip show
pip list
```

### Result

Neither package was installed in the runtime Python environment.

### Decision

The findings were documented rather than introducing unnecessary dependencies.

---

# 16. Screenshots

Evidence captured during this phase includes:

```text
phase-06-01-repository-scan-timeout.png
phase-06-02-trivy-repository-scan.png
phase-06-03-trivy-report-summary.png
phase-06-04-python-vulnerabilities.png
phase-06-05-fixable-vulnerabilities.png
phase-06-06-python-security-scan.png
phase-06-07-runtime-python-packages.png
phase-06-08-precise-library-scan.png
```

Additional GitHub Actions screenshots will be added after the security workflow is validated on the pull request.

---

# 17. Key Learnings

This phase provided hands-on experience with:

* DevSecOps
* Shift-left security
* Trivy
* Vulnerability scanning
* Container image scanning
* Secret scanning
* Misconfiguration scanning
* CVE analysis
* Severity classification
* Runtime dependency verification
* False-positive investigation
* SBOM-related findings
* Security baselines
* Security gates
* Docker security
* GitHub Actions security automation
* Risk-based vulnerability remediation

---

# 18. Security Investigation Method

The main process followed during this phase was:

```text
Detect
   ↓
Verify
   ↓
Analyze Runtime Impact
   ↓
Check Remediation Availability
   ↓
Remediate or Document
   ↓
Re-test
   ↓
Re-scan
```

A scanner result should not automatically lead to random dependency changes.

The actual runtime environment must be verified before remediation.

---

# 19. Interview Explanation

I implemented security scanning for my Enterprise DevSecOps Platform using Trivy.

I scanned both the source repository and the Docker image for HIGH and CRITICAL vulnerabilities, secrets, and configuration issues.

During repository scanning, Trivy initially timed out because it traversed the local Python virtual environment. I resolved this by excluding `.venv` and increasing the timeout.

The initial container image scan also identified multiple Debian vulnerabilities. I used `--ignore-unfixed` to separate vulnerabilities that currently had available vendor fixes from those that did not.

Trivy also reported two Python package vulnerabilities for msgpack and setuptools. Instead of directly modifying the application, I verified the actual runtime container using `pip show` and `pip list`. Neither package was present in the runtime environment, so I documented those findings rather than introducing unnecessary dependencies.

Finally, I added Trivy scanning to GitHub Actions so repository and container security checks can run automatically during pushes and pull requests.

This phase helped me understand how DevSecOps combines vulnerability detection, verification, remediation decisions, automation, and continuous security validation.

---

# 20. Final Phase 6 Flow

```text
Developer
    ↓
Git Feature Branch
    ↓
Pytest
    ↓
Docker Build
    ↓
Trivy Repository Scan
    ├── Vulnerabilities
    ├── Secrets
    └── Misconfigurations
    ↓
Trivy Container Scan
    ├── OS Packages
    └── Python Libraries
    ↓
Runtime Verification
    ↓
Security Analysis
    ↓
GitHub Actions
    ↓
Pull Request
    ↓
Security Review
    ↓
Merge
```

---

## Current Status

* Repository security scanning implemented
* Container security scanning implemented
* Security reports generated
* Runtime findings verified
* Application regression testing passed
* GitHub Actions security workflow created
* Security documentation completed

The next step is to push the `feature/security-scanning` branch, create a pull request, validate the GitHub Actions security jobs, capture final workflow screenshots, and merge the feature into `main`.
