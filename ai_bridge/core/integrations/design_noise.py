
import random
from typing import Any, Dict

class DesignNoiseGenerator:
    """Generates stochastic design parameters to ensure unique UI outputs."""
    
    PALETTES = [
        ["#0F172A", "#3B82F6", "#F8FAFC"], # Slate & Blue
        ["#171717", "#DC2626", "#FFFFFF"], # Dark & Red
        ["#FFFFFF", "#059669", "#1F2937"], # Clean & Green
        ["#1E293B", "#8B5CF6", "#F1F5F9"]  # Dark & Violet
    ]
    
    TYPOGRAPHY = ["sans-inter", "serif-lora", "mono-jetbrains"]
    
    RADIUS = ["0px", "4px", "8px", "16px", "24px"]
    
    SHADOWS = ["none", "sm", "md", "lg", "xl"]

    @classmethod
    def generate(cls) -> Dict[str, Any]:
        return {
            "palette": random.choice(cls.PALETTES),
            "font": random.choice(cls.TYPOGRAPHY),
            "radius": random.choice(cls.RADIUS),
            "shadow": random.choice(cls.SHADOWS),
            "noise_factor": random.uniform(0.1, 0.4)
        }
