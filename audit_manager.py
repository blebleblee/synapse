import os
from learning_engine.models import AnthropicProvider

def run_audit():
    with open('learning_engine/topic_manager.py', 'r') as f:
        code = f.read()
    
    with open('audit_prompt.txt', 'r') as f:
        prompt_text = f.read()

    # Create a specific prompt for topic_manager
    specific_prompt = prompt_text.replace("generator.py - Part 2", "topic_manager.py")
    
    prov = AnthropicProvider(model='claude-3-5-sonnet-20241022')
    full_prompt = f"{specific_prompt}\n\nLook for:\n1. Robustness of curriculum taxonomy (L1-L4 structure).\n2. Security risks in path handling.\n3. Scalability of topic tree generation.\n4. Maintainability.\n\nMODULE CONTENT:\n{code[:15000]}"
    
    print(prov.generate(full_prompt, system_instruction='You are a ruthless technical auditor.'))

if __name__ == "__main__":
    run_audit()
