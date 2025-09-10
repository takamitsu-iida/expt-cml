#!/bin/bash

sudo -s -E

NODE_DEF_ROOT=/var/lib/libvirt/images/node-definitions
NODE_DEF_FILENAME=tig.yaml

IMAGE_DEF_ROOT=/var/lib/virl2/images/node_definitions
IMAGE_DEF_DIR=tig
IMAGE_DEF_FILENAME=tig.yaml
IMAGE_NAME=tig.tar.gz

mv /var/tmp/node_definition.yaml ${NODE_DEF_ROOT}/${NODE_DEF_FILENAME}
chown libvirt-qemu:virl2 ${NODE_DEF_ROOT}/${NODE_DEF_FILENAME}

mkdir -p ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}
mv /var/tmp/image_definition.yaml ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}/${IMAGE_DEF_FILENAME}
mv /var/tmp/${IMAGE_NAME} ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}/${IMAGE_NAME}
chown -R libvirt-qemu:virl2 ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}
