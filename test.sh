#!/bin/bash
VERSION=$(git rev-parse --short --verify HEAD)
./build.sh
./install.sh "$VERSION"