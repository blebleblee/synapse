import os
from learning_engine.models import AnthropicProvider

def run_audit():
    with open('learning_engine/cli.py', 'r') as f:
        code = f.read()
    
    # Audit prompt for cli.py
    prompt = f'''You are an adversarial Senior Software Architect & Security Auditor. Audit the following Python module (learning_engine/cli.py).

Look for:
1. Command-line interface design (UX/ergonomics).
2. Security risks in command execution (subprocesses, user input validation).
3. Robustness of server orchestration (Uvicorn integration).
4. Error handling and logging.

Provide a concise, high-signal audit report with actionable refactoring recommendations.

MODULE CONTENT:
{code[:15000]}
'''
    
    prov = AnthropicProvider(model='claude-3-5-sonnet-20241022')
    print(prov.generate(prompt, system_instruction='You are a ruthless technical auditor.'))

if __name__ == "__main__":
    run_audit()
