.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


####################################################
# 以下、変更不要
####################################################
SOURCE_IMAGE_DEFINITION = cml_image_definition.yaml
SOURCE_NODE_DEFINITION = cml_node_definition.yaml
INSTALL_SCRIPT = cml_install_image.sh
SSH_OPTS = -p 1122 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
CONTAINER_NAME = ntools-test

lab: ## ラボをCML上に作成する
	../bin/cml_create_jumphost.py --create

stop: ## ラボを停止する
	../bin/cml_create_jumphost.py --stop

delete: ## ラボを削除する
	../bin/cml_create_jumphost.py --delete

upload: ## arcosの初期設定ファイルをjumphostにアップロードする
	# @rsync -avz -e "ssh ${SSH_OPTS}" $(IMAGE_TAR_GZ) image_definition.yaml node_definition.yaml ${INSTALL_SCRIPT} admin@${CML_HOST}:${CML_UPLOAD_DIR}
