.PHONY: help
HELP_FUN = fprintf(out,"%%-25s %%s\n",(char[]){$1,64-$1},$$2);

# ==============================================================================
# NRG Sovereign Landing - Makefile
# NIC/MeitY Infrastructure Deployment Targets
# ==============================================================================

HELP_FORMAT = "%-25s %s\n"
SHELL = /bin/bash
.DELETE_ON_ERROR:
.PHONY: help

## help: Display this help message
help:
	@printf "NRG Sovereign Landing - Deployment Makefile\n\n"
	@printf "Usage: make [target]\n\n"
	@printf "Targets:\n"
	@printf "$(HELP_FORMAT)" "deploy-staging" "Deploy to staging environment"
	@printf "$(HELP_FORMAT)" "deploy-prod" "Deploy to production environment"
	@printf "$(HELP_FORMAT)" "deploy-canary" "Deploy canary (10% traffic)"
	@printf "$(HELP_FORMAT)" "deploy-blue-green" "Deploy blue-green switchover"
	@printf "$(HELP_FORMAT)" "rollback" "Rollback to previous version"
	@printf "$(HELP_FORMAT)" "rollback-full" "Full rollback via Helm"
	@printf "$(HELP_FORMAT)" "verify" "Verify deployment health"
	@printf "$(HELP_FORMAT)" "smoke-test" "Run smoke tests"
	@printf "$(HELP_FORMAT)" "backup" "Trigger manual backup"
	@printf "$(HELP_FORMAT)" "disaster-recover" "Start disaster recovery"
	@printf "$(HELP_FORMAT)" "destroy" "Destroy all NRG resources"
	@printf "\n"

## deploy-staging: Deploy to staging environment
deploy-staging:
	@echo "Deploying to staging..."
	helm upgrade --install nrg-staging ./infrastructure/helm/nrg \
		--namespace nrg-staging \
		--create-namespace \
		-f ./infrastructure/helm/nrg/values.staging.yaml \
		--wait --timeout=10m
	@echo "Staging deployment complete"

## deploy-prod: Deploy to production environment
deploy-prod:
	@echo "Deploying to production..."
	helm upgrade --install nrg ./infrastructure/helm/nrg \
		--namespace nrg-production \
		--create-namespace \
		-f ./infrastructure/helm/nrg/values.prod.yaml \
		--wait --timeout=15m
	@echo "Production deployment complete"

## deploy-canary: Deploy canary with 10% traffic
deploy-canary:
	@echo "Deploying canary (10% traffic)..."
	python3 ./infrastructure/helm/nrg/scripts/sovereign_deploy.py \
		--version $(VERSION) \
		--strategy canary \
		--canary-weight 10 \
		--namespace nrg-production

## deploy-blue-green: Deploy with blue-green strategy
deploy-blue-green:
	@echo "Deploying with blue-green strategy..."
	python3 ./infrastructure/helm/nrg/scripts/sovereign_deploy.py \
		--version $(VERSION) \
		--strategy blue-green \
		--namespace nrg-production

## rollback: Rollback to previous version
rollback:
	@echo "Rolling back..."
	kubectl rollout undo deployment/nrg-api -n nrg-production
	kubectl rollout undo deployment/nrg-kong -n nrg-production

## rollback-full: Full Helm rollback
rollback-full:
	@echo "Full Helm rollback..."
	helm rollback nrg -n nrg-production

## verify: Verify deployment health
verify:
	@echo "Verifying deployment..."
	@kubectl rollout status deployment/nrg-api -n nrg-production --timeout=120s
	@kubectl rollout status deployment/nrg-postgres -n nrg-production --timeout=120s
	@kubectl rollout status deployment/nrg-qdrant -n nrg-production --timeout=120s
	@kubectl rollout status deployment/nrg-redis -n nrg-production --timeout=120s
	@kubectl rollout status deployment/nrg-kong -n nrg-production --timeout=120s
	@kubectl get hpa -n nrg-production
	@kubectl get pdb -n nrg-production
	@echo "Deployment verified"

## smoke-test: Run smoke tests
smoke-test:
	@echo "Running smoke tests..."
	@curl -sf http://nrg-api:8000/health/live && echo " - /health/live OK"
	@curl -sf http://nrg-api:8000/health/ready && echo " - /health/ready OK"
	@curl -sf http://nrg-api:8000/health && echo " - /health OK"
	@echo "Smoke tests passed"

## backup: Trigger manual backup
backup:
	@echo "Triggering manual backup..."
	kubectl create job nrg-manual-backup-$(shell date +%Y%m%d%H%M%S) \
		--namespace nrg-production \
		--from=cronjob/nrg-postgres-backup
	@echo "Backup job created"

## disaster-recover: Start disaster recovery
disaster-recover:
	@echo "Starting disaster recovery..."
	bash ./infrastructure/sovereign/disaster_recovery.sh full

## destroy: Destroy all NRG resources
destroy:
	@echo "WARNING: This will destroy all NRG resources!"
	@read -p "Are you sure? Type 'yes': " confirm && [ "$$confirm" = "yes" ]
	helm uninstall nrg -n nrg-production || true
	kubectl delete namespace nrg-production --ignore-not-found=true
	helm uninstall nrg-staging -n nrg-staging || true
	kubectl delete namespace nrg-staging --ignore-not-found=true