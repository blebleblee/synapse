import test from 'node:test';
import assert from 'node:assert/strict';
import { synthesizeTerminalCommand } from './commandSynthesizer.ts';

test('synthesizeTerminalCommand - bash shell commands execute directly', () => {
  const result = synthesizeTerminalCommand('ls -la /var/log', 'bash');
  assert.equal(result.isExecutable, true);
  assert.equal(result.command, 'ls -la /var/log');
  assert.equal(result.displayLabel, '▶ Run Command');
});

test('synthesizeTerminalCommand - SQL queries wrapped with psql/sqlite3 runner', () => {
  const query = 'SELECT datname, numbackends FROM pg_stat_database;';
  const result = synthesizeTerminalCommand(query, 'sql');
  assert.equal(result.isExecutable, true);
  assert.equal(result.displayLabel, '▶ Run SQL');
  assert.match(result.command, /cat << 'EOF' > \/tmp\/synapse_query\.sql/);
  assert.match(result.command, /psql/);
  assert.match(result.command, /sqlite3/);
});

test('synthesizeTerminalCommand - Kubernetes manifests applied via kubectl', () => {
  const yaml = `apiVersion: v1\nkind: Pod\nmetadata:\n  name: test-pod`;
  const result = synthesizeTerminalCommand(yaml, 'yaml');
  assert.equal(result.isExecutable, true);
  assert.equal(result.displayLabel, '▶ Apply K8s Manifest');
  assert.match(result.command, /kubectl apply -f \/tmp\/synapse_manifest\.yaml/);
});

test('synthesizeTerminalCommand - Generic YAML saved to config', () => {
  const yaml = `server:\n  port: 8080\n  host: 0.0.0.0`;
  const result = synthesizeTerminalCommand(yaml, 'yaml');
  assert.equal(result.isExecutable, true);
  assert.equal(result.displayLabel, '▶ Save YAML');
  assert.match(result.command, /\/tmp\/synapse_config\.yaml/);
});

test('synthesizeTerminalCommand - Python scripts executed via venv python', () => {
  const py = `import sys\nprint(sys.version)`;
  const result = synthesizeTerminalCommand(py, 'python');
  assert.equal(result.isExecutable, true);
  assert.equal(result.displayLabel, '▶ Run Python');
  assert.match(result.command, /\/tmp\/synapse_script\.py/);
  assert.match(result.command, /\.venv\/bin\/python3/);
});

test('synthesizeTerminalCommand - C programs compiled and run', () => {
  const c = `#include <stdio.h>\nint main() { printf("ok\\n"); return 0; }`;
  const result = synthesizeTerminalCommand(c, 'c');
  assert.equal(result.isExecutable, true);
  assert.equal(result.displayLabel, '▶ Compile & Run C');
  assert.match(result.command, /gcc -O2/);
});

test('synthesizeTerminalCommand - Non-executable languages fallback safely', () => {
  const text = `Just some notes`;
  const result = synthesizeTerminalCommand(text, 'markdown');
  assert.equal(result.isExecutable, false);
});

test('shell run tooltip does not claim a sandbox (the Host Shell profile may be active)', () => {
  const synth = synthesizeTerminalCommand('ls -la', 'bash');
  assert.ok(!/sandbox terminal/.test(synth.explanation));
  assert.match(synth.explanation, /terminal panel/);
});
