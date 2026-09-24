SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE := docker compose

.PHONY: help up up-vpn down restart build reload rebuild init-dirs certs ps logs \
        sandbox-build sandbox-shell sandbox-reset mcp-shell \
        vpn-status data-size clear-logs clean

help: ## Show this help
	@printf "\033[1mLibre Box — available targets:\033[0m\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_%-]+:.*?## / {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start the stack
	$(MAKE) init-dirs
	$(MAKE) certs
	$(COMPOSE) up -d

up-vpn: ## Start the stack with the VPN overlay
	$(MAKE) init-dirs
	$(MAKE) certs
	$(COMPOSE) -f docker-compose.yml -f docker-compose.vpn.yml up -d

down: ## Stop and remove containers
	$(COMPOSE) down --remove-orphans

restart: ## Restart all services
	$(COMPOSE) restart

build: ## Build local images
	$(COMPOSE) build

reload: ## Rebuild changed images and recreate services
	$(MAKE) init-dirs
	$(MAKE) certs
	$(COMPOSE) build
	$(COMPOSE) up -d

rebuild: ## Clean rebuild (down + build --no-cache + up)
	$(COMPOSE) down
	$(COMPOSE) build --no-cache
	$(MAKE) init-dirs
	$(MAKE) certs
	$(COMPOSE) up -d

init-dirs: ## Create host bind-mount directories
	@mkdir -p data logs/librechat logs/nginx logs/mcp
	@chown 1000:1000 data logs/librechat 2>/dev/null || chmod 0777 data logs/librechat 2>/dev/null || true

certs: ## Generate a self-signed TLS cert for local dev (skips if present)
	@if [ -f nginx/certs/fullchain.pem ] && [ -f nginx/certs/privkey.pem ]; then \
		echo "TLS cert already present in nginx/certs/"; \
	else \
		echo "Generating self-signed TLS cert in nginx/certs/"; \
		MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -sha256 -days 365 -nodes -keyout nginx/certs/privkey.pem -out nginx/certs/fullchain.pem -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1"; \
	fi

ps: ## Show container status
	$(COMPOSE) ps

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

logs-%: ## Tail logs for one service (e.g. make logs-mcp)
	$(COMPOSE) logs -f $*

sandbox-build: ## Build the sandbox image
	$(COMPOSE) build sandbox

sandbox-shell: ## Open a login shell inside the sandbox
	$(COMPOSE) exec sandbox bash -l

sandbox-reset: ## Reset the sandbox to a clean OS (keeps /root/data)
	$(COMPOSE) up -d --force-recreate sandbox

mcp-shell: ## Open a shell inside the MCP container
	$(COMPOSE) exec mcp /bin/sh

vpn-status: ## Show the sandbox public egress IP (through VPN if enabled)
	$(COMPOSE) exec sandbox bash -lc 'curl -s https://ifconfig.me; echo'

data-size: ## Show the size of the shared data workspace
	@du -sh data 2>/dev/null || echo "data/ is empty"

clear-logs: ## Clear the host log files under logs/ (deletes them when the stack is down)
	@if [ ! -d logs ]; then \
		echo "No logs/ directory to clear"; \
	elif running=$$($(COMPOSE) ps -q --status running 2>/dev/null) && [ -z "$$running" ]; then \
		find logs -type f -delete 2>/dev/null; \
		if [ -z "$$(find logs -type f 2>/dev/null)" ]; then \
			echo "Removed host log files under logs/"; \
		else \
			echo "Some files under logs/ could not be removed, retry with sudo"; \
			exit 1; \
		fi; \
	elif find logs -type f -exec truncate -s 0 {} + 2>/dev/null; then \
		echo "Truncated host log files under logs/, the files stay in place"; \
	else \
		echo "Some files under logs/ are not writable, retry with sudo"; \
		exit 1; \
	fi

clean: ## Remove containers AND volumes (DESTROYS DATA). Requires CONFIRM=yes
	@[ "$(CONFIRM)" = "yes" ] || { echo "Refusing without CONFIRM=yes"; exit 1; }
	$(COMPOSE) down -v --remove-orphans