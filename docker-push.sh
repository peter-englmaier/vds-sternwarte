#!/bin/bash
if [ -n "$1" ]; then
  docker tag penglmaier/vds-sternwarte penglmaier/vds-sternwarte:$1
fi
docker push penglmaier/vds-sternwarte:${1-latest}
