import test from 'node:test';
import assert from 'node:assert/strict';
import { sanitizeAndRepairMermaid } from './mermaidRepair.ts';

test('quoted edge labels lose the spaces Mermaid rejects around them', () => {
  assert.equal(
    sanitizeAndRepairMermaid('graph LR\n  A -->| "Submit YAML" | B\n  C -.->|"ok" | D'),
    'graph LR\n  A -->|"Submit YAML"| B\n  C -.->|"ok"| D',
  );
});

test('semicolons in sequence messages and notes are kept as text', () => {
  assert.equal(
    sanitizeAndRepairMermaid('sequenceDiagram\n  A->>B: BEGIN; UPDATE row\n  Note over A,B: fsync; then ack\n  B-->>A: ok'),
    'sequenceDiagram\n  A->>B: BEGIN\u037e UPDATE row\n  Note over A,B: fsync\u037e then ack\n  B-->>A: ok',
  );
});

test('flowcharts keep their statement semicolons handling', () => {
  assert.equal(sanitizeAndRepairMermaid('graph TD;\n  A --> B;'), 'graph TD\n  A --> B');
});

test('sequence text keeps existing entities such as #9829;', () => {
  assert.equal(sanitizeAndRepairMermaid('sequenceDiagram\n  A->>B: I #9829; you'), 'sequenceDiagram\n  A->>B: I #9829; you');
});
