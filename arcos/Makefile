.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# ラボタイトル
LAB_TITLE = arcos_test_lab


####################################################
# 以下、変更不要
####################################################
SOURCE_IMAGE_DEFINITION = cml_image_definition.yaml
SOURCE_NODE_DEFINITION = cml_node_definition.yaml
INSTALL_SCRIPT = cml_install_image.sh
SSH_OPTS = -p 1122 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
CONTAINER_NAME = ntools-test

jumphost: ## 踏み台サーバをCML上に作成する
	../bin/cml_create_jumphost.py --create --title "$(LAB_TITLE)"
	../bin/cml_create_jumphost.py --start

upload: ## 踏み台サーバに設定ファイルをアップロードする
	../bin/cml_create_arcos_lab.py --upload

stop: ## ラボを停止する
	../bin/cml_create_jumphost.py --stop --title "$(LAB_TITLE)"

delete: ## ラボを削除する
	../bin/cml_create_jumphost.py --delete --title "$(LAB_TITLE)"

ztp: ## arcosの初期設定ファイルをjumphostにアップロードし、ZTPを実行する
	../bin/cml_create_jumphost.py --ztp --title "$(LAB_TITLE)"

upload: ## arcosの初期設定ファイルをjumphostにアップロードする
	# @rsync -avz -e "ssh ${SSH_OPTS}" $(IMAGE_TAR_GZ) image_definition.yaml node_definition.yaml ${INSTALL_SCRIPT} admin@${CML_HOST}:${CML_UPLOAD_DIR}
