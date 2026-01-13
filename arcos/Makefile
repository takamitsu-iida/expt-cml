.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# 作成するラボタイトル
LAB_TITLE = arcos_test_lab

# 作成するラボのデスクリプション
DESCRIPTION = arcos lab for testing

jumphost: ## 踏み台サーバをCML上に作成する
	../bin/cml_create_jumphost.py --create --title "$(LAB_TITLE)" --description "$(DESCRIPTION)"

upload: ## 踏み台サーバに設定ファイルをアップロードする（踏み台サーバ起動後に実行すること）
	../bin/cml_create_arcos_lab.py --upload

arcos: ## arcosノードをCML上に作成する
	../bin/cml_create_arcos_lab.py --create --title "$(LAB_TITLE)"

start: ## ラボを開始する
	../bin/cml_create_jumphost.py --start --title "$(LAB_TITLE)"

stop: ## ラボを停止する
	../bin/cml_create_jumphost.py --stop --title "$(LAB_TITLE)"

delete: ## ラボを削除する
	../bin/cml_create_jumphost.py --delete --title "$(LAB_TITLE)"

terminal: ## ルータのコンソールに接続する
	../bin/open_terminal.sh 6001 6002
	../bin/open_terminal.sh 6011 6012
	../bin/open_terminal.sh 6013 6014

browse: ## ブラウザにノードのコンソールURLを表示する
	../bin/cml_create_arcos_lab.py --browse --title "$(LAB_TITLE)"