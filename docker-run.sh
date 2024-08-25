#!/bin/bash
echo "Access local instance on http://localhost:5000"
docker run --rm -t -i -v ./instance:/vds/instance -v ./config.json:/vds/config.json:ro -p 5000:5000 penglmaier/vds-sternwarte
