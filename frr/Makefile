.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

TAG ?= frr:10.4

IMAGE_DEFINITION_DIR = /var/lib/libvirt/images/virl-base-images/frr-10-4/
SOURCE_IMAGE_DEFINITION = cml_image_definition.yaml

CML_HOST = 192.168.122.212
SCP_OPTS = -P 1122 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
CONTAINER_NAME = frr-iida


build: ## Dockerイメージを作成する
	@docker build -t ${TAG} -f Dockerfile .


inspect: ## DockerイメージのIDをインスペクトして、image_definition.yamlのsha256を更新する
	@cp -f ${SOURCE_IMAGE_DEFINITION} image_definition.yaml
	@SHA256=$$(docker inspect ${TAG} | grep -o 'sha256:[0-9a-f]\{64\}' | head -n 1 | cut -d: -f2); \
	sed -i "s/^sha256:.*/sha256: $$SHA256/" image_definition.yaml; \
	echo $$SHA256


save: ## Dockerイメージを保存する
	@rm -f frr.tar.gz
	@docker save -o frr.tar ${TAG}
	@gzip frr.tar


run: ## Dockerコンテナを起動する
	@docker run -d --rm --init --privileged --name ${CONTAINER_NAME} ${TAG}


shell: ## Dockerコンテナにシェルで入る
	@docker exec -it ${CONTAINER_NAME} bash


stop: ## Dockerコンテナを停止する
	@if [ -n "$$(docker ps -q -f name=${CONTAINER_NAME})" ]; then docker stop ${CONTAINER_NAME}; fi


prune: ## Dockerの不要なイメージを削除する
	@docker system prune -f --all


clean: ## Dockerイメージを削除する
	@if [ -n "$$(docker images -q)" ]; then docker rmi $$(docker images -q); fi
	@rm -f frr.tar.gz
	@rm -f image_definition.yaml


upload: ## frr.tar.gzをCMLのイメージ定義のディレクトリにアップロードする
	@scp ${SCP_OPTS} frr.tar.gz admin@${CML_HOST}:${IMAGE_DEFINITION_DIR}
	@scp ${SCP_OPTS} image_definition.yaml admin@${CML_HOST}:${IMAGE_DEFINITION_DIR}