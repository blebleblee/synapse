/**
 * Smart Terminal Command Synthesizer
 * Context-aware code executor that wraps SQL queries, Kubernetes manifests,
 * Python scripts, C/Rust programs, and shell commands into safe, self-contained
 * terminal executions instead of raw, error-prone shell pastes.
 */

export interface SynthesizedCommand {
  command: string;
  displayLabel: string;
  isExecutable: boolean;
  explanation: string;
}

export function synthesizeTerminalCommand(code: string, lang: string): SynthesizedCommand {
  const language = (lang || '').trim().toLowerCase();
  const trimmed = code.trim();

  // 1. Bash / Shell commands
  if (['bash', 'sh', 'zsh', 'shell'].includes(language)) {
    return {
      command: trimmed,
      displayLabel: '▶ Run Command',
      isExecutable: true,
      explanation: 'Runs this command in the terminal panel (the profile selected there: sandbox or host shell).'
    };
  }

  // 2. SQL queries (PostgreSQL / SQLite)
  if (['sql', 'psql'].includes(language)) {
    const wrapped = `cat << 'EOF' > /tmp/synapse_query.sql\n${trimmed}\nEOF\nif command -v psql >/dev/null 2>&1; then\n  psql -U postgres -d postgres -f /tmp/synapse_query.sql 2>/dev/null || psql -f /tmp/synapse_query.sql\nelif command -v sqlite3 >/dev/null 2>&1; then\n  sqlite3 /tmp/synapse.db < /tmp/synapse_query.sql\nelse\n  echo "[✔] Saved SQL query to /tmp/synapse_query.sql (Run with: psql -f /tmp/synapse_query.sql)"\nfi`;
    return {
      command: wrapped,
      displayLabel: '▶ Run SQL',
      isExecutable: true,
      explanation: 'Saves query to /tmp/synapse_query.sql and executes against active database.'
    };
  }

  // 3. Kubernetes / YAML Manifests
  if (['yaml', 'yml', 'k8s', 'kubernetes'].includes(language)) {
    const isK8s = trimmed.includes('apiVersion:') || trimmed.includes('kind:') || trimmed.includes('metadata:');
    if (isK8s) {
      const wrapped = `cat << 'EOF' > /tmp/synapse_manifest.yaml\n${trimmed}\nEOF\nif command -v kubectl >/dev/null 2>&1; then\n  kubectl apply -f /tmp/synapse_manifest.yaml\nelse\n  echo "[✔] Saved Kubernetes manifest to /tmp/synapse_manifest.yaml (Apply with: kubectl apply -f /tmp/synapse_manifest.yaml)"\nfi`;
      return {
        command: wrapped,
        displayLabel: '▶ Apply K8s Manifest',
        isExecutable: true,
        explanation: 'Saves manifest to /tmp/synapse_manifest.yaml and applies via kubectl.'
      };
    } else {
      const wrapped = `cat << 'EOF' > /tmp/synapse_config.yaml\n${trimmed}\nEOF\necho "[✔] Saved YAML configuration to /tmp/synapse_config.yaml"`;
      return {
        command: wrapped,
        displayLabel: '▶ Save YAML',
        isExecutable: true,
        explanation: 'Saves YAML configuration to /tmp/synapse_config.yaml.'
      };
    }
  }

  // 4. Python scripts
  if (['python', 'py', 'python3'].includes(language)) {
    const wrapped = `cat << 'EOF' > /tmp/synapse_script.py\n${trimmed}\nEOF\nif [ -f "$PWD/.venv/bin/python3" ]; then\n  "$PWD/.venv/bin/python3" /tmp/synapse_script.py\nelse\n  python3 /tmp/synapse_script.py\nfi`;
    return {
      command: wrapped,
      displayLabel: '▶ Run Python',
      isExecutable: true,
      explanation: 'Saves script to /tmp/synapse_script.py and executes via virtualenv Python.'
    };
  }

  // 5. C / C++ programs
  if (['c', 'cpp'].includes(language)) {
    const wrapped = `cat << 'EOF' > /tmp/synapse_app.c\n${trimmed}\nEOF\ngcc -O2 /tmp/synapse_app.c -o /tmp/synapse_app -lm && /tmp/synapse_app`;
    return {
      command: wrapped,
      displayLabel: '▶ Compile & Run C',
      isExecutable: true,
      explanation: 'Compiles /tmp/synapse_app.c with gcc and runs the resulting binary.'
    };
  }

  // 6. Rust programs
  if (['rust', 'rs'].includes(language)) {
    const wrapped = `cat << 'EOF' > /tmp/synapse_app.rs\n${trimmed}\nEOF\nrustc /tmp/synapse_app.rs -o /tmp/synapse_app_rs && /tmp/synapse_app_rs`;
    return {
      command: wrapped,
      displayLabel: '▶ Compile & Run Rust',
      isExecutable: true,
      explanation: 'Compiles /tmp/synapse_app.rs with rustc and executes the binary.'
    };
  }

  // 7. JSON data files
  if (['json'].includes(language)) {
    const wrapped = `cat << 'EOF' > /tmp/synapse_data.json\n${trimmed}\nEOF\nif command -v jq >/dev/null 2>&1; then\n  jq . /tmp/synapse_data.json\nelse\n  python3 -m json.tool /tmp/synapse_data.json\nfi`;
    return {
      command: wrapped,
      displayLabel: '▶ Inspect JSON',
      isExecutable: true,
      explanation: 'Saves to /tmp/synapse_data.json and formats with jq.'
    };
  }

  return {
    command: trimmed,
    displayLabel: '▶ Send to Terminal',
    isExecutable: false,
    explanation: 'Sends raw snippet to the terminal.'
  };
}
