.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

TAG ?= ubuntu24:frr10.5

build: ## Dockerイメージを作成する
	@docker build -t ${TAG} -f Dockerfile .


save: ## Dockerイメージを保存する
	@docker save -o frr.tar ${TAG}


run: ## Dockerコンテナを起動する
	@docker run -d --rm --init --privileged --name frr ${TAG}


shell: ## Dockerコンテナにシェルで入る
	@docker exec -it frr bash


stop: ## Dockerコンテナを停止する
	@docker stop frr


clean: ## Dockerイメージを削除する
	@docker rm -f $(docker ps -aq)
	@docker rmi $(docker images -q)
