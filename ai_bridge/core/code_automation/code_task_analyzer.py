class CodeTaskAnalyzer:
    def analyze(self, text: str) -> dict:
        return {"intent": "code_change", "text": text}
