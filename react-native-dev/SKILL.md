---
name: react-native-dev
description: React Native 0.7x dev, Jest test mocks, and Yarn CLI fixes.
version: 1.0.0
---

# React Native 0.7x Development & Testing

## Overview
Guidelines and proven workarounds for React Native 0.7x projects using Yarn 1.x / Corepack, Jest, React Navigation, and TypeScript.

## Key Pitfalls & Workarounds

### 1. React Native 0.72 Jest Setup & Native Mocks
- **Jest Preset & Setup File**: React Native 0.72 includes native Jest setup at `node_modules/react-native/jest/setup.js`. Include it in `jest.config.js`:
  ```javascript
  setupFiles: ['./node_modules/react-native/jest/setup.js'],
  setupFilesAfterEnv: ['./jest.setup.js'],
  ```
- **React Navigation `BackHandler` Mocking**: `@react-navigation/native` uses `useBackButton` which listens to `BackHandler.addEventListener`. If `BackHandler` is unmocked in test renderer environments, Jest throws `TypeError: _reactNative.BackHandler.addEventListener is not a function` during environment teardown.
  Mock `useBackButton` or `NavigationContainer` in `jest.setup.js`:
  ```javascript
  jest.mock('@react-navigation/native', () => {
    const actualNav = jest.requireActual('@react-navigation/native');
    return {
      ...actualNav,
      NavigationContainer: ({children}) => children,
      useBackButton: jest.fn(),
    };
  });
  ```
- **AsyncStorage Mock**:
  ```javascript
  import mockAsyncStorage from '@react-native-async-storage/async-storage/jest/async-storage-mock';
  jest.mock('@react-native-async-storage/async-storage', () => mockAsyncStorage);
  ```

### 2. Yarn 1.x & `node_modules/.bin` Binary Linking Issues
- When running Yarn 1 under Node 22 via Corepack, nested CLI binaries (e.g. `jest`, `eslint`) might not be linked into `node_modules/.bin/` if only parent packages (like `react-native`) depend on them.
- **Fix**: Explicitly add top-level CLI packages to `devDependencies`:
  ```bash
  yarn add -D jest@29.7.0 jest-cli@29.7.0 eslint@8.19.0 @react-native/eslint-config@0.72.2 @react-native/metro-config@0.72.11 react-test-renderer@18.2.0
  ```

### 3. Missing Metro & ESLint Configuration Dependencies
- **Metro Config**: If bundling fails with `Cannot find module '@react-native/metro-config'`, explicitly install `@react-native/metro-config@0.72.11`.
- **ESLint Config**: If `eslint` fails with `ESLint couldn't find the config "@react-native" to extend from`, ensure `@react-native/eslint-config@0.72.2` is in `devDependencies`.

### 4. Verification Commands
- **Metro Bundle Verification**: Test bundle creation without launching an emulator:
  ```bash
  npx react-native bundle --platform ios --dev true --entry-file index.js --bundle-output /tmp/main.jsbundle
  ```
- **Metro Dev Server API Test**:
  ```bash
  curl -s "http://127.0.0.1:8081/index.bundle?platform=ios&dev=true" | head -n 20
  ```
