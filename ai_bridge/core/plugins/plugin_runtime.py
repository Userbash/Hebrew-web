class PluginRuntimeService:
    def invoke(self, plugin_name: str, payload: dict):
        return {"plugin": plugin_name, "payload": payload, "status": "ok"}
