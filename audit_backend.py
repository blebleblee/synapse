import os
from learning_engine.models import AnthropicProvider

def run_audit():
    with open('app/backend/main.py', 'r') as f:
        code = f.read()
    
    # Audit prompt for main.py
    prompt = f'''You are an adversarial Senior Software Architect & Security Auditor. Audit the following Python module (app/backend/main.py).

Look for:
1. API Security (input validation, SQL injection, RCE vulnerabilities, CORS).
2. Robustness of PTY/Terminal WebSocket management.
3. Concurrency hazards in global state management (e.g., GLOBAL_TERMINAL_BUFFER).
4. Error handling and logging.

Provide a concise, high-signal audit report with actionable refactoring recommendations.

MODULE CONTENT:
{code[:15000]}
'''
    
    prov = AnthropicProvider(model='claude-3-5-sonnet-20241022')
    print(prov.generate(prompt, system_instruction='You are a ruthless technical auditor.'))

if __name__ == "__main__":
    run_audit()
