#!/usr/bin/env bash

./make-cstv-dir.sh
# cp -r ./content/* /opt/cstv
sudo rsync -avu --delete content/ /opt/cstv/
