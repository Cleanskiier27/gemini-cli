#!/usr/bin/env node
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 *
 * A tiny launcher that forwards its arguments to the installed gcloud CLI.
 * Build this into afterburner.exe with pkg, nexe, or another bundler.
 */

import { spawn } from 'node:child_process';
import process from 'node:process';

const args = process.argv.slice(2);
const command = process.platform === 'win32' ? 'gcloud.cmd' : 'gcloud';

function exitWithError(message) {
  process.stderr.write(`Error: ${message}\n`);
  process.exit(1);
}

const child = spawn(command, args, {
  stdio: 'inherit',
  shell: false,
  env: process.env,
});

child.on('error', (error) => {
  if (error && typeof error.message === 'string') {
    if (error.message.includes('ENOENT')) {
      exitWithError('gcloud executable not found. Please install Google Cloud SDK and ensure it is on PATH.');
    }
    exitWithError(error.message);
  }
  exitWithError('Failed to launch gcloud.');
});

child.on('close', (code) => {
  process.exit(code ?? 0);
});
