#!/bin/bash

docker build -t penglmaier/vds-sternwarte . || exit $?

docker push penglmaier/vds-sternwarte

docker run -v ./instance:/vds/instance -v ./config.json:/vds/config.json:ro -p 5000:5000 penglmaier/vds-sternwarte
