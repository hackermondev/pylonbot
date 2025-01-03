#!/bin/bash

apt-get -y update
apt-get install -y wget unzip

rm -rf /tmp/protoc
mkdir /tmp/protoc

wget https://github.com/protocolbuffers/protobuf/releases/download/v3.11.2/protoc-3.11.2-linux-x86_64.zip
unzip protoc-3.11.2-linux-x86_64.zip -d /tmp/protoc

mv /tmp/protoc/bin/protoc /usr/bin/protoc

