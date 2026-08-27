.PHONY: craft-up craft-down craft-sandbox-image craft-backend-image craft-refresh-images craft-check-images desktop desktop-down

# Local single-user Onyx: no login screen, ports bound to localhost only.
# See deployment/docker_compose/docker-compose.desktop.yml.
desktop:
	docker compose -f deployment/docker_compose/docker-compose.yml \
	               -f deployment/docker_compose/docker-compose.desktop.yml \
	               --project-directory deployment/docker_compose up -d --wait

desktop-down:
	docker compose -f deployment/docker_compose/docker-compose.yml \
	               -f deployment/docker_compose/docker-compose.desktop.yml \
	               --project-directory deployment/docker_compose down

craft-up:
	deployment/helm/dev/craft-up.sh

craft-down:
	deployment/helm/dev/craft-down.sh

craft-sandbox-image:
	docker build -t onyxdotapp/sandbox:dev backend/onyx/server/features/build/sandbox/image
	kind load docker-image onyxdotapp/sandbox:dev --name onyx-dev

# Rebuild the image the in-cluster sandbox-proxy/api-server run, then restart them.
craft-backend-image:
	docker build -t onyxdotapp/onyx-backend:dev backend/
	kind load docker-image onyxdotapp/onyx-backend:dev --name onyx-dev
	kubectl rollout restart deploy/onyx-sandbox-proxy deploy/onyx-api-server -n onyx

# Refresh everything: backend + sandbox images, PodTemplate, proxy/api restart.
craft-refresh-images:
	deployment/helm/dev/refresh-images.sh

craft-check-images:
	deployment/helm/dev/refresh-images.sh --check || true
