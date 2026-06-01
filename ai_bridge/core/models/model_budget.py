class TokenBudgetManagerImpl:
    def estimate(self, text: str) -> int:
        return max(1, len(text)//4)
    def can_fit(self, model: str, input_tokens: int, reserved_output_tokens: int = 1024) -> bool:
        window = 8000 if model == "local-small" else 128000
        return input_tokens + reserved_output_tokens <= window
