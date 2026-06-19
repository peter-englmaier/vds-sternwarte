#!/bin/bash
# specify options if needed (i.e. --no-cache)
LOCAL=vds-sternwarte


# is build clean?
if [ $(git diff | wc -l) -eq 0 ]; then
	CLEANBUILD=true
else
	CLEANBUILD=false
fi

# do we have a tag?
GITCOMMIT=$(git show --pretty=format:"%h" --no-patch)
GITCOMMITLONG=$(git show --pretty=format:"%H" --no-patch)

# what version is this?
if $CLEANBUILD; then 
	APPVERSION=$(git tag --points-at $GITCOMMITLONG)
	echo "APPVERSION='$APPVERSION'"
	if $CLEANBUILD && [ $APPVERSION != ""]; then
		echo "Clean Build of version $APPVERSION"
	else
		echo "UNCLEAN Build (Version: $APPVERSION)"
	fi
else
	APPVERSION=""
fi

# BUILD
if [ "$APPVERSION" != "" ]; then
	TAGS="-t $LOCAL -t $LOCAL:$APPVERSION"
else
	TAGS="-t $LOCAL"
fi
echo "TAGS='$TAGS'"
echo "docker build --build-arg CLEANBUILD=$CLEANBUILD \\"
echo "  --build-arg GITCOMMIT=$GITCOMMIT \\"
echo "  --build-arg GITCOMMITLONG=$GITCOMMITLONG \\"
echo "  --build-arg APPVERSION=$APPVERSION \\"
echo "  $TAGS . $@"
docker build --build-arg CLEANBUILD=$CLEANBUILD \
--build-arg GITCOMMIT=$GITCOMMIT --build-arg GITCOMMITLONG=$GITCOMMITLONG \
--build-arg APPVERSION=$APPVERSION \
$TAGS . $@
