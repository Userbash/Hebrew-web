class NativeModelRouter:
    def select_model(self, task, context):
        _ = context
        if getattr(task, "type", None) and str(task.type).endswith("REVIEW"):
            return {"provider": "openai", "model": "gpt-4o"}
        return {"provider": "local", "model": "local-small"}
