import os
from learning_engine.models import AnthropicProvider

def run_audit():
    with open('learning_engine/generator.py', 'r') as f:
        code_lines = f.readlines()
        code_part2 = "".join(code_lines[500:]) # Part 2
    
    with open('audit_prompt.txt', 'r') as f:
        prompt_text = f.read()

    prov = AnthropicProvider(model='claude-3-5-sonnet-20241022')
    full_prompt = f"{prompt_text}\n\nMODULE CONTENT (Part 2):\n{code_part2[:15000]}"
    
    print(prov.generate(full_prompt, system_instruction='You are a ruthless technical auditor.'))

if __name__ == "__main__":
    run_audit()
