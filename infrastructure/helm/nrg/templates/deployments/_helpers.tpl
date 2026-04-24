apiVersion: v1
kind: ServiceAccount
metadata:
  name: nrg-sa
  namespace: {{ .Values.namespace | default "nrg-production" }}
  labels:
    app: nrg
    app.kubernetes.io/name: nrg
    app.kubernetes.io/component: service-account
  annotations:
    nrg.gov.in/compliance: mandatory
    nrg.gov.in/data-classification: confidential
    # Vault Agent: this SA is used for Kubernetes auth to Vault
    vault.hashicorp.com/role: {{ .Values.vault.role | default "nrg-app" }}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: nrg-secret-reader
  namespace: {{ .Values.namespace | default "nrg-production" }}
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list"]
    resourceNames:
      - nrg-tls-cert
      - nrg-registry-secret
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: nrg-secret-reader-binding
  namespace: {{ .Values.namespace | default "nrg-production" }}
subjects:
  - kind: ServiceAccount
    name: nrg-sa
    namespace: {{ .Values.namespace | default "nrg-production" }}
roleRef:
  kind: Role
  name: nrg-secret-reader
  apiGroup: rbac.authorization.k8s.io