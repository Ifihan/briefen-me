#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Get environment from command line args
const environment = process.argv[2] || 'production';

if (!['production', 'development'].includes(environment)) {
  console.error('Invalid environment. Use "production" or "development"');
  process.exit(1);
}

const BUILD_DIR = 'extension-build';
const SOURCE_DIR = 'chrome-extension';

console.log(`Building Chrome Extension for ${environment}...`);

// Clean previous build
if (fs.existsSync(BUILD_DIR)) {
  fs.rmSync(BUILD_DIR, { recursive: true });
}
fs.mkdirSync(BUILD_DIR, { recursive: true });

// Copy all files from chrome-extension to build directory
function copyDir(src, dest) {
  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      fs.mkdirSync(destPath, { recursive: true });
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

copyDir(SOURCE_DIR, BUILD_DIR);

// Update config.js with the correct environment
const configPath = path.join(BUILD_DIR, 'config.js');
let configContent = fs.readFileSync(configPath, 'utf8');
configContent = configContent.replace(
  /environment: ['"].*['"]/,
  `environment: '${environment}'`
);
fs.writeFileSync(configPath, configContent);

// Update manifest.json for production
if (environment === 'production') {
  const manifestPath = path.join(BUILD_DIR, 'manifest.json');
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

  // Remove localhost from host_permissions
  manifest.host_permissions = manifest.host_permissions.filter(
    permission => !permission.includes('localhost')
  );

  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
}

// Create zip file
const zipFile = `briefen-me-extension-${environment}.zip`;
try {
  // Remove old zip if exists
  if (fs.existsSync(zipFile)) {
    fs.unlinkSync(zipFile);
  }

  // Create new zip
  if (process.platform === 'win32') {
    // Windows - use PowerShell
    execSync(`powershell Compress-Archive -Path ${BUILD_DIR}\\* -DestinationPath ${zipFile}`, { stdio: 'inherit' });
  } else {
    // Unix-like systems
    execSync(`cd ${BUILD_DIR} && zip -r ../${zipFile} .`, { stdio: 'inherit' });
  }
} catch (error) {
  console.error('Warning: Could not create zip file. You may need to install zip utility.');
  console.error('You can still use the files in the build directory.');
}

console.log('\nBuild complete!');
console.log(`Extension files: ${BUILD_DIR}/`);
console.log(`Zip file: ${zipFile}`);
console.log('\nTo load the extension in Chrome:');
console.log('1. Go to chrome://extensions/');
console.log('2. Enable "Developer mode"');
console.log('3. Click "Load unpacked"');
console.log(`4. Select the "${BUILD_DIR}" folder`);