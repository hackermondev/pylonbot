#!/bin/bash

./setup_protoc.sh
export PATH=$PATH:$GOPATH/bin

echo "Clearing old Go stubs"

cd go/rpc/
rm -R -- */
cd ../../

echo "Building GO stubs..."

protoc -Iproto --go_out=plugins=grpc:. $(find proto -type f -name "*.proto" | grep -v proto/google)

echo "Moving from build dir..."
mv ./up.lol/pylon/rpc/go/rpc/* ./go/rpc/
rm -rf ./up.lol

echo "...Done!"
