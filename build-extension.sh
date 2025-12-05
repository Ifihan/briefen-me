#!/bin/bash
set -e

# Build script for Chrome Extension
# Usage: ./build-extension.sh [production|development]

ENVIRONMENT=${1:-production}
BUILD_DIR="extension-build"

echo "Building Chrome Extension for ${ENVIRONMENT}..."

# Clean previous build
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# Copy all extension files
cp -r chrome-extension/* "${BUILD_DIR}/"

# Update config.js with the correct environment
sed -i.bak "s/environment: '.*'/environment: '${ENVIRONMENT}'/" "${BUILD_DIR}/config.js"
rm "${BUILD_DIR}/config.js.bak"

# Remove localhost host_permissions for production
if [ "$ENVIRONMENT" = "production" ]; then
  # Use a different approach for sed that works on both macOS and Linux
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's/"http:\/\/localhost:5001\/\*",//g' "${BUILD_DIR}/manifest.json"
    sed -i '' 's/,\s*"http:\/\/localhost:5001\/\*"//g' "${BUILD_DIR}/manifest.json"
  else
    # Linux
    sed -i 's/"http:\/\/localhost:5001\/\*",//g' "${BUILD_DIR}/manifest.json"
    sed -i 's/,\s*"http:\/\/localhost:5001\/\*"//g' "${BUILD_DIR}/manifest.json"
  fi
fi

# Create a zip file for submission
cd "${BUILD_DIR}"
zip -r "../briefen-me-extension-${ENVIRONMENT}.zip" .
cd ..

echo "Build complete!"
echo "Extension files: ${BUILD_DIR}/"
echo "Zip file: briefen-me-extension-${ENVIRONMENT}.zip"
echo ""
echo "To load the extension in Chrome:"
echo "1. Go to chrome://extensions/"
echo "2. Enable 'Developer mode'"
echo "3. Click 'Load unpacked'"
echo "4. Select the '${BUILD_DIR}' folder"