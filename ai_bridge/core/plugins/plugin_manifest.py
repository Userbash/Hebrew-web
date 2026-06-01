from pydantic import BaseModel
class PluginManifest(BaseModel):
    name: str
    version: str = "0.1.0"
    permissions: list[str] = []
