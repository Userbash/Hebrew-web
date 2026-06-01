from ai_bridge.core.integrations.registry import IntegrationRegistry
from .sandbox_policy import DEFAULT_DENY
class PluginManager:
    def __init__(self, registry: IntegrationRegistry) -> None:
        self.registry = registry
        self.permissions = dict(DEFAULT_DENY)
    def register_plugin(self, module):
        return self.registry.register(module)
