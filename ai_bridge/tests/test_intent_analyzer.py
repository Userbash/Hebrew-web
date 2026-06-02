from ai_bridge.core.intent_analyzer_module import IntentAnalyzerModule
from unittest.mock import MagicMock

def test_intent_analyzer_parsing():
    # Setup mock API
    mock_api = MagicMock()
    analyzer = IntentAnalyzerModule()
    analyzer.on_load(mock_api)
    
    # Test prompt
    prompt = "Create a minimalist landing page for a language school"
    
    # Run analysis
    result = analyzer.analyze_user_prompt(prompt)
    
    # Validate result
    assert result.layout == "bento-grid"
    assert result.primary_color == "#2A5C82"
    assert "HeroSection" in result.components
    assert result.vibe == "minimalist"
    
    print("Test passed: IntentAnalyzerModule parsed the prompt correctly.")

if __name__ == "__main__":
    test_intent_analyzer_parsing()
