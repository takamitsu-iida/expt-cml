.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


build: ## Dockerイメージを作成する
	docker build \
		--build-arg=UBUNTU_VERSION=24.04 \
		-t ubuntu24:frr10.5 \
		-f Dockerfile .
