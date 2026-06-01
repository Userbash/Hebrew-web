from .prompt_contracts import NormalizedPrompt

def normalize(raw_user_input: str) -> NormalizedPrompt:
    text = " ".join(raw_user_input.strip().split())
    return NormalizedPrompt(original_text=raw_user_input, cleaned_text=text, user_intent="general", task_type="code")
