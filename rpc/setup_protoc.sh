#!/bin/bash

echo "Setting up protoc-gen-go (GOPATH: $GOPATH)"
go get -u github.com/golang/protobuf/protoc-gen-go
