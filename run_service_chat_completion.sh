#!/usr/bin/env bash

# Load env vars
export $(grep -v '^#' .env | xargs)

echo "OPENAI_API_KEY = $OPENAI_API_KEY"

make clean

autonomy push-all

autonomy fetch --local --service algovera/chat_completion_local && cd chat_completion_local

# Build the image
autonomy build-image

# Copy keys and build the deployment
cp /path/to/your/keys.json ./keys.json

autonomy deploy build -ltm

# Run the deployment
autonomy deploy run --build-dir abci_build/