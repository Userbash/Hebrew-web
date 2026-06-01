class PatchValidator:
    def validate(self, diff_text: str) -> bool:
        return bool(diff_text.strip())
