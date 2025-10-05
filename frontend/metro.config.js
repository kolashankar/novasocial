// metro.config.js
const { getDefaultConfig } = require("expo/metro-config");
const path = require('path');
const { FileStore } = require('metro-cache');

const config = getDefaultConfig(__dirname);

// Use a stable on-disk store (shared across web/android)
const root = process.env.METRO_CACHE_ROOT || path.join(__dirname, '.metro-cache');
config.cacheStores = [
  new FileStore({ root: path.join(root, 'cache') }),
];


// Exclude unnecessary directories from file watching
config.watchFolders = [__dirname];
config.resolver.blockList = /(.*)\/(__tests__|android|ios|build|dist|.git|node_modules\/.*\/android|node_modules\/.*\/ios|node_modules\/.*\/windows|node_modules\/.*\/macos|node_modules\/.*\/debugger-frontend|node_modules\/.*\/third-party)(\/.*)?$/;

// Reduce the number of workers to decrease resource usage
config.maxWorkers = 1;

module.exports = config;
