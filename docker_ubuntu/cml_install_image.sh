#!/bin/bash

NODE_DEF_ROOT=/var/lib/libvirt/images/node-definitions
NODE_DEF_FILENAME=ubuntu-24-04-docker.yaml

IMAGE_DEF_ROOT=/var/lib/libvirt/images/virl-base-images
IMAGE_DEF_DIR=ubuntu-24-04-docker
IMAGE_DEF_FILENAME=ubuntu-24-04-docker.yaml
IMAGE_NAME=ubuntu24.04.20251010.tar.gz

if [ -f /var/tmp/node_definition.yaml ]; then
    mv /var/tmp/node_definition.yaml ${NODE_DEF_ROOT}/${NODE_DEF_FILENAME}
    chown libvirt-qemu:virl2 ${NODE_DEF_ROOT}/${NODE_DEF_FILENAME}
else
    echo "node_definition.yaml not found."
fi

mkdir -p ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}

if [ -f /var/tmp/image_definition.yaml ]; then
    mv /var/tmp/image_definition.yaml ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}/${IMAGE_DEF_FILENAME}
else
    echo "image_definition.yaml not found."
fi

if [ -f /var/tmp/${IMAGE_NAME} ]; then
    mv /var/tmp/${IMAGE_NAME} ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}/${IMAGE_NAME}
else
    echo "${IMAGE_NAME} not found."
fi

chown -R libvirt-qemu:virl2 ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}

# スクリプト自身を削除
rm -- "$0"
