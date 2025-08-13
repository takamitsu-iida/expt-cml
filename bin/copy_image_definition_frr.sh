#!/bin/bash

# 本スクリプトはgithubにおいてあるので、このコマンドをコックピットのターミナルで実行する
# curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/bin/copy_image_definition_frr.sh | bash -s

# 特権ユーザのシェルを取る
# パスワードを聞かれる
sudo -s -E

COPY_SRC="ubuntu-24-04-20250503"
COPY_DST="ubuntu-24-04-20250503-frr"

IMAGE_DEF_ID=${COPY_DST}
IMAGE_DEF_LABEL="Ubuntu 24.04 - 3 May 2025 with frr installed"

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
sed -i -e "s/^id:.*\$/id: ${IMAGE_DEF_ID}/" ${COPY_DST}.yaml
sed -i -e "s/^label:.*\$/label: ${IMAGE_DEF_LABEL}/" ${COPY_DST}.yaml
sed -i -e "s/^description:.*\$/description: ${IMAGE_DEF_LABEL}/" ${COPY_DST}.yaml
sed -i -e "s/^read_only:.*\$/read_only: false/" ${COPY_DST}.yaml

# virl2を再起動する
systemctl restart virl2.target

cat ${COPY_DST}.yaml
