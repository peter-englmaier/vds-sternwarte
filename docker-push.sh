#!/bin/bash
REGISTRY=docker.io
REPOSITORY=penglmaier/vds-sternwarte
LOCAL=vds-sternwarte
REMOTE=$REGISTRY/$REPOSITORY


# what version is this?
if [ $(git diff | wc -l) -eq 0 ]; then
  GITCOMMITLONG=$(git show --pretty=format:"%H" --no-patch)
  APPVERSION=$(git tag --points-at $GITCOMMITLONG)
else
  APPVERSION=""
fi

echo docker tag $LOCAL:latest $REMOTE:latest
docker tag $LOCAL:latest $REMOTE:latest
echo docker push $REMOTE:latest
docker push $REMOTE:latest
if [ "$APPVERSION" != "" ]; then
  echo docker tag $REMOTE $REMOTE:$APPVERSION
  docker tag $REMOTE $REMOTE:$APPVERSION
  echo docker push $REMOTE:$APPVERSION
  docker push $REMOTE:$APPVERSION
fi
