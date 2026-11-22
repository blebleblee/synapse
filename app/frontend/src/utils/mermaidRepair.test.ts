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

test('brackets inside an already quoted label are left alone', () => {
  const src = 'graph TD\n  TP1["GPU 0<br/>W[:, 0:d/2]"] --> E["E[Y|X=x] = mean"]';
  assert.equal(sanitizeAndRepairMermaid(src), src);
});

test('unquoted labels with special characters still get quoted', () => {
  assert.equal(sanitizeAndRepairMermaid('graph TD\n  A[f(x) = y] --> B'), 'graph TD\n  A["f(x) = y"] --> B');
});

test('unquoted edge labels with spaces or brackets get quoted on any arrow', () => {
  assert.equal(
    sanitizeAndRepairMermaid('graph LR\n  L -->|row[column.key]| K\n  B1 -.->|V(t) Updates<br/>Only| B1\n  X ==>|two words| Y\n  P -->|ok| Q'),
    'graph LR\n  L -->|"row[column.key]"| K\n  B1 -.->|"V(t) Updates<br/>Only"| B1\n  X ==>|"two words"| Y\n  P -->|ok| Q',
  );
});

test('a malformed arrow end does not double-quote a quoted label', () => {
  assert.equal(sanitizeAndRepairMermaid('graph LR\n  A1 -->|"stdout or file" |> B1'), 'graph LR\n  A1 -->|"stdout or file"| B1');
});
