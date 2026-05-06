#!/bin/bash

# This installs uv

curl -LsSf https://astral.sh/uv/install.sh | sh

uv python install 3.14.4
