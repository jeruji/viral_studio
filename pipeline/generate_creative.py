from llm.prompts import SYSTEM_PROMPT

def generate_creative(llm, brief):
    return llm.generate_creative(SYSTEM_PROMPT, brief)
