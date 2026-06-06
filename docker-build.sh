#!/bin/bash
# specify options if needed (i.e. --no-cache)
LOCAL=vds-sternwarte

echo docker build -t $LOCAL . $@
docker build -t $LOCAL . $@
