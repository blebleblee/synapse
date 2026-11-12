import os
from learning_engine.models import AnthropicProvider

def run_comprehensive_audit():
    # Load all critical modules
    modules = {
        "generator.py": "learning_engine/generator.py",
        "models.py": "learning_engine/models.py",
        "topic_manager.py": "learning_engine/topic_manager.py",
        "cli.py": "learning_engine/cli.py",
        "main.py": "app/backend/main.py"
    }
    
    code_content = ""
    for name, path in modules.items():
        with open(path, 'r') as f:
            code_content += f"\n--- {name} ---\n{f.read()}\n"
    
    # Audit prompt
    prompt = f'''You are a Senior Security Architect. Perform a final, comprehensive audit of the entire synapse codebase.

1. Verify that the fixes applied (Path Traversal sanitization, Thread safety/locking, Domain-specific LaTeX constraints, SSE streaming) have correctly closed the previously identified vulnerabilities.
2. Identify ANY remaining critical vulnerabilities (P0) or architectural blockers.
3. Assess the system's readiness for production.

CODEBASE CONTENT:
{code_content[:15000]}
'''
    
    prov = AnthropicProvider(model='claude-3-5-sonnet-20241022')
    print(prov.generate(prompt, system_instruction='You are a ruthless technical security auditor.'))

if __name__ == "__main__":
    run_comprehensive_audit()
