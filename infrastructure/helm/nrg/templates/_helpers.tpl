{{/* vim: set noexpandtab: */}}
{{/*
Common labels for NRG resources
*/}}
{{- define "nrg.labels" -}}
app.kubernetes.io/name: nrg
app.kubernetes.io/managed-by: Helm
app.kubernetes.io/part-of: nrg-platform
nrg.gov.in/compliance: mandatory
nrg.gov.in/data-classification: confidential
{{- end }}

{{/*
Selector labels for NRG resources
*/}}
{{- define "nrg.selectors" -}}
app: nrg
app.kubernetes.io/name: nrg
{{- end }}

{{/*
API labels
*/}}
{{- define "nrg.api.labels" -}}
{{ include "nrg.labels" }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Vault agent annotations for secret injection
*/}}
{{- define "nrg.vault.annotations" -}}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: {{ .Values.vault.role | default "nrg-app" }}
vault.hashicorp.com/agent-inject-default: "false"
vault.hashicorp.com/agent-inject-file: "secrets.env"
vault.hashicorp.com/agent-inject-template: |
  {{ "{{" }}- with secret "secret/data/nrg/production" -{{ "}}" }}
  DATABASE_URL=postgresql://{{ "{{" }} .Data.data.db_user {{ "}}" }}:{{ "{{" }} .Data.data.db_password {{ "}}" }}@{{ .Values.postgresql.host }}:5432/{{ .Values.postgresql.database }}
  DATABASE_POOL_MIN=20
  DATABASE_POOL_MAX=40
  REDIS_URL=redis://{{ .Values.redis.host }}:6379/0
  QUERY_RESULT_CACHE_TTL_SECONDS=300
  QDRANT_HOST={{ .Values.qdrant.host }}
  QDRANT_PORT={{ .Values.qdrant.port }}
  AUDIT_AUTO_REPAIR_LINE1=false
  TRUST_PROXY_HEADERS=true
  JWT_SECRET={{ "{{" }} .Data.data.jwt_secret {{ "}}" }}
  API_ENCRYPTION_KEY={{ "{{" }} .Data.data.api_encryption_key {{ "}}" }}
  {{ "{{" }}- end {{ "}}" }}
{{- end }}

{{/*
Security context for pods (restricted PSS)
*/}}
{{- define "nrg.podSecurityContext" -}}
securityContext:
  fsGroup: 1000
  fsGroupChangePolicy: "OnRootMismatch"
  seccompProfile:
    type: "RuntimeDefault"
  supplementalGroups: [1000]
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
{{- end }}

{{/*
Container security context (restricted PSS)
*/}}
{{- define "nrg.containerSecurityContext" -}}
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
{{- end }}
