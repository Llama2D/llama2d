#!/bin/bash

URL=`git config --get remote.origin.url | sed 's/\.git//g'`
BRANCH=`git rev-parse --abbrev-ref HEAD`
FILE=$1

echo $URL/blob/$BRANCH/$FILE
echo $URL/$FILE
exit 0