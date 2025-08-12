#!/bin/bash

# 本スクリプトはgithubにおいてあるので、このコマンドで実行する
# curl -Ls https://raw.githubusercontent.com/takamitsu-iida/frr-on-cml/refs/heads/main/bin/copy_node_definition.sh | bash -s

# 特権ユーザのシェルを取る
# パスワードを聞かれる
sudo -s -E

COPY_SRC="ubuntu-24-04-20241004"
COPY_DST="ubuntu-24-04-20241004-frr"

NODE_DEF_ID=${COPY_DST}
NODE_DEF_LABEL="Ubuntu 24.04 - 04 Oct 2024 FRR installed"

# ubuntuイメージのある場所に移動する
cd /var/lib/libvirt/images/virl-base-images

# すでにターゲットのディレクトリがあるなら消す
rm -rf ${COPY_DST}

# 属性付きでubuntuディレクトリをコピー
cp -a ${COPY_SRC} ${COPY_DST}

# オーナーをvirl2にする
chown virl2:virl2 ${COPY_DST}

# 作成したディレクトリに移動
cd ${COPY_DST}

# ノード定義ファイルの名前をディレクトリ名と一致させる
mv ${COPY_SRC}.yaml ${COPY_DST}.yaml

# ノード定義ファイルを編集する
sed -i -e "s/^id:.*\$/id: ${NODE_DEF_ID}/" ${COPY_DST}.yaml
sed -i -e "s/^label:.*\$/label: ${NODE_DEF_LABEL}/" ${COPY_DST}.yaml
sed -i -e "s/^description:.*\$/description: ${NODE_DEF_LABEL}/" ${COPY_DST}.yaml

systemctl restart virl2.target

cat ${COPY_DST}.yaml
