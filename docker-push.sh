#!/bin/bash
REGISTRY=docker.io
REPOSITORY=penglmaier/vds-sternwarte
LOCAL=vds-sternwarte
REMOTE=$REGISTRY/$REPOSITORY

echo docker tag $LOCAL:latest $REMOTE:latest
docker tag $LOCAL:latest $REMOTE:latest
echo docker push $REMOTE:latest
docker push $REMOTE:latest
if [ -n "$1" ]; then
  echo docker tag $REMOTE $REMOTE:$1
  docker tag $REMOTE $REMOTE:$1
  echo docker push $REMOTE:$1
  docker push $REMOTE:$1
fi
