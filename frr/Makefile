.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

TAG ?= frr:10.4

IMAGE_DEFINITION_DIR = /var/lib/libvirt/images/virl-base-images/frr-10-4/

build: ## Dockerイメージを作成する
	@docker build -t ${TAG} -f Dockerfile .


inspect: ## DockerイメージのIDをインスペクトする
	# @docker inspect ${TAG} | grep -i sha256 | head -n 1 | awk '{print $$2}'
    @docker inspect ${TAG} | grep -i sha256 | head -n 1 | awk -F: '{print $$2}' | tr -d '", '

save: ## Dockerイメージを保存する
	@rm -f frr.tar.gz
	@docker save -o frr.tar ${TAG}
	@gzip frr.tar


run: ## Dockerコンテナを起動する
	@docker run -d --rm --init --privileged --name frr-iida ${TAG}


shell: ## Dockerコンテナにシェルで入る
	@docker exec -it frr-iida bash


stop: ## Dockerコンテナを停止する
	@docker stop frr-iida


prune: ## Dockerの不要なイメージを削除する
	@docker system prune -f --all


clean: ## Dockerイメージを削除する
	@docker rmi $$(docker images -q)
	@rm -f frr.tar.gz


upload: ## frr.tar.gzをCMLのイメージ定義のディレクトリにアップロードする
	@scp -P 1122 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null frr.tar.gz admin@192.168.122.212:${IMAGE_DEFINITION_DIR}