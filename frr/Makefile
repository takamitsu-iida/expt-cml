.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

TAG ?= frr:10.5-iida

build: ## Dockerイメージを作成する
	@docker build -t ${TAG} -f Dockerfile .


inspect: ## DockerイメージのIDをインスペクトする
	@docker inspect ${TAG} | grep -i sha256 | head -n 1 | awk '{print $$2}'


save: ## Dockerイメージを保存する
	@docker save -o frr.tar ${TAG}


run: ## Dockerコンテナを起動する
	@docker run -d --rm --init --privileged --name frr-iida ${TAG}


shell: ## Dockerコンテナにシェルで入る
	@docker exec -it frr-iida bash


stop: ## Dockerコンテナを停止する
	@docker stop frr-iida


clean: ## Dockerイメージを削除する
	@docker rm -f $(docker ps -aq)
	@docker rmi $(docker images -q)
