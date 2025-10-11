.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

TAG ?= tig:latest

# CMLのIPアドレス
CML_HOST = 192.168.122.212
CML_UPLOAD_DIR = /var/tmp

####################################################
# 【事前準備】
####################################################
#
# make upload ではscpでファイルをCMLに送り込みますので、
# CMLのadminユーザに対して公開鍵認証を設定しておく必要があります。
#
# 鍵を作っていない場合
# ssh-keygen -t rsa -b 4096 -N "" -f ~/.ssh/id_rsa
#
# 公開鍵をCMLに登録
# ssh-copy-id -p 1122 admin@192.168.122.212

####################################################
# 以下、変更不要
####################################################
SOURCE_IMAGE_DEFINITION = cml_image_definition.yaml
SOURCE_NODE_DEFINITION = cml_node_definition.yaml
INSTALL_SCRIPT = cml_install_image.sh
SSH_OPTS = -p 1122 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
CONTAINER_NAME = tig-test

# --build-argで渡す引数 (TOKENはランダムな32桁の文字列)
BUILD_ARGS = --build-arg TOKEN=$$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)


build: ## Dockerイメージを作成する
	@docker build -t ${TAG} ${BUILD_ARGS} -f Dockerfile .


inspect: ## DockerイメージのIDをインスペクトして、image_definition.yamlおよびnode_definition.yamlを生成する
	@cp -f ${SOURCE_IMAGE_DEFINITION} image_definition.yaml
	@cp -f ${SOURCE_NODE_DEFINITION} node_definition.yaml
	@SHA256=$$(docker inspect ${TAG} | grep -o 'sha256:[0-9a-f]\{64\}' | head -n 1 | cut -d: -f2); \
	sed -i "s/^sha256:.*/sha256: $$SHA256/" image_definition.yaml; echo $$SHA256

	@INDENT='          '; \
	sed "s/^/$$INDENT/" cfg/telegraf.conf > telegraf_conf_indented.txt; \
	awk '/__TELEGRAF_CONF__/ {system("cat telegraf_conf_indented.txt"); next} {print}' node_definition.yaml > node_definition.yaml.tmp; \
	mv node_definition.yaml.tmp node_definition.yaml; \
	rm -f telegraf_conf_indented.txt;

	@INDENT='          '; \
	sed "s/^/$$INDENT/" cfg/influxdb.conf > influxdb_conf_indented.txt; \
	awk '/__INFLUXDB_CONF__/ {system("cat influxdb_conf_indented.txt"); next} {print}' node_definition.yaml > node_definition.yaml.tmp; \
	mv node_definition.yaml.tmp node_definition.yaml; \
	rm -f influxdb_conf_indented.txt;

	@INDENT='          '; \
	sed "s/^/$$INDENT/" cfg/grafana.ini > grafana_ini_indented.txt; \
	awk '/__GRAFANA_INI__/ {system("cat grafana_ini_indented.txt"); next} {print}' node_definition.yaml > node_definition.yaml.tmp; \
	mv node_definition.yaml.tmp node_definition.yaml; \
	rm -f grafana_ini_indented.txt;

	@INDENT='          '; \
	sed "s/^/$$INDENT/" cfg/supervisord.conf > supervisord_conf_indented.txt; \
	awk '/__SUPERVISORD_CONF__/ {system("cat supervisord_conf_indented.txt"); next} {print}' node_definition.yaml > node_definition.yaml.tmp; \
	mv node_definition.yaml.tmp node_definition.yaml; \
	rm -f supervisord_conf_indented.txt;


save: ## Dockerイメージを保存する
	@rm -f tig.tar.gz
	@docker save -o tig.tar ${TAG}
	@gzip tig.tar


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
	@rm -f tig.tar
	@rm -f image_definition.yaml
	@rm -f node_definition.yaml


upload: ## tig.tarおよびノード定義ファイルをCMLにアップロードする
	@rsync -avz -e "ssh ${SSH_OPTS}" tig.tar.gz image_definition.yaml node_definition.yaml ${INSTALL_SCRIPT} admin@${CML_HOST}:${CML_UPLOAD_DIR}
