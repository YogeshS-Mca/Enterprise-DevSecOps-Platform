{{/*
Chart name
*/}}
{{- define "enterprise-devsecops.name" -}}
enterprise-devsecops
{{- end }}

{{/*
Application workload name
*/}}
{{- define "enterprise-devsecops.fullname" -}}
enterprise-devsecops-app
{{- end }}

{{/*
Chart identification
*/}}
{{- define "enterprise-devsecops.chart" -}}
{{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end }}

{{/*
Stable selector labels.

Keep this selector intentionally minimal because the Helm release
is adopting the Kubernetes Deployment originally created in Phase 7.
*/}}
{{- define "enterprise-devsecops.selectorLabels" -}}
app: enterprise-devsecops-app
{{- end }}