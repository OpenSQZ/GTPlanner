"""
Unit tests for language detection module.

This module tests all language detection functionality including:
- Detection of different languages
- Edge cases and boundary conditions
- Error handling
- Helper functions
"""

import pytest
from utils.language_detection import (
    LanguageDetector,
    SupportedLanguage,
    detect_language,
    is_supported_language,
    get_supported_languages,
    language_detector
)


class TestLanguageDetector:
    """Test suite for LanguageDetector class."""

    def test_init_default_language(self):
        """Test initialization with default language."""
        detector = LanguageDetector()
        assert detector.default_language == SupportedLanguage.ENGLISH

    def test_init_custom_default_language(self):
        """Test initialization with custom default language."""
        detector = LanguageDetector(default_language=SupportedLanguage.CHINESE)
        assert detector.default_language == SupportedLanguage.CHINESE

    def test_detect_english_text(self):
        """Test detection of English text."""
        detector = LanguageDetector()
        
        # Simple English text
        text = "Hello world, this is a test."
        assert detector.detect_language(text) == SupportedLanguage.ENGLISH
        
        # Technical English text
        text = "The system should implement authentication and authorization."
        assert detector.detect_language(text) == SupportedLanguage.ENGLISH

    def test_detect_chinese_text(self):
        """Test detection of Chinese text."""
        detector = LanguageDetector()
        
        # Simplified Chinese
        text = "这是一个中文测试。"
        assert detector.detect_language(text) == SupportedLanguage.CHINESE
        
        # Mixed Chinese and English
        text = "这是一个测试 with some English words"
        result = detector.detect_language(text)
        # Should detect Chinese due to Chinese character weight
        assert result == SupportedLanguage.CHINESE

    def test_detect_japanese_text(self):
        """Test detection of Japanese text."""
        detector = LanguageDetector()
        
        # Japanese with Hiragana
        text = "こんにちは、世界。これはテストです。"
        assert detector.detect_language(text) == SupportedLanguage.JAPANESE
        
        # Japanese with Katakana
        text = "テストデータです。"
        assert detector.detect_language(text) == SupportedLanguage.JAPANESE

    def test_detect_spanish_text(self):
        """Test detection of Spanish text."""
        detector = LanguageDetector()
        
        text = "Hola mundo, esto es una prueba."
        result = detector.detect_language(text)
        assert result == SupportedLanguage.SPANISH

    def test_detect_french_text(self):
        """Test detection of French text."""
        detector = LanguageDetector()
        
        text = "Bonjour le monde, c'est un test."
        result = detector.detect_language(text)
        assert result == SupportedLanguage.FRENCH

    def test_detect_empty_text(self):
        """Test detection with empty text."""
        detector = LanguageDetector()
        
        # Empty string
        assert detector.detect_language("") == SupportedLanguage.ENGLISH
        
        # Whitespace only
        assert detector.detect_language("   ") == SupportedLanguage.ENGLISH
        
        # None would fail, but empty string should work
        assert detector.detect_language("") == detector.default_language

    def test_user_preference_override(self):
        """Test that user preference overrides detection."""
        detector = LanguageDetector()
        
        # Chinese text with English preference
        text = "这是中文文本"
        result = detector.detect_language(text, user_preference="en")
        assert result == SupportedLanguage.ENGLISH
        
        # English text with Chinese preference
        text = "This is English text"
        result = detector.detect_language(text, user_preference="zh")
        assert result == SupportedLanguage.CHINESE

    def test_invalid_user_preference(self):
        """Test handling of invalid user preference."""
        detector = LanguageDetector()
        
        # Invalid preference should fall back to detection
        text = "这是中文文本"
        result = detector.detect_language(text, user_preference="invalid")
        assert result == SupportedLanguage.CHINESE

    def test_chinese_vs_japanese_detection(self):
        """Test disambiguation between Chinese and Japanese."""
        detector = LanguageDetector()
        
        # Japanese text with kanji (Chinese characters) and hiragana
        japanese_text = "日本語のテキストです"
        result = detector.detect_language(japanese_text)
        assert result == SupportedLanguage.JAPANESE
        
        # Pure Chinese text
        chinese_text = "这是纯中文文本"
        result = detector.detect_language(chinese_text)
        assert result == SupportedLanguage.CHINESE

    def test_is_supported_language(self):
        """Test language support checking."""
        detector = LanguageDetector()
        
        # Valid languages
        assert detector.is_supported_language("en") == True
        assert detector.is_supported_language("zh") == True
        assert detector.is_supported_language("ja") == True
        assert detector.is_supported_language("es") == True
        assert detector.is_supported_language("fr") == True
        
        # Case insensitive
        assert detector.is_supported_language("EN") == True
        assert detector.is_supported_language("ZH") == True
        
        # Invalid languages
        assert detector.is_supported_language("de") == False
        assert detector.is_supported_language("invalid") == False
        assert detector.is_supported_language("") == False

    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        detector = LanguageDetector()
        
        languages = detector.get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) == 5
        assert "en" in languages
        assert "zh" in languages
        assert "ja" in languages
        assert "es" in languages
        assert "fr" in languages

    def test_get_language_name(self):
        """Test getting language names."""
        detector = LanguageDetector()
        
        assert detector.get_language_name("en") == "English"
        assert detector.get_language_name("zh") == "中文"
        assert detector.get_language_name("ja") == "日本語"
        assert detector.get_language_name("es") == "Español"
        assert detector.get_language_name("fr") == "Français"
        
        # Case insensitive
        assert detector.get_language_name("EN") == "English"
        
        # Unknown language
        assert detector.get_language_name("unknown") == "Unknown"


class TestGlobalFunctions:
    """Test suite for global convenience functions."""

    def test_detect_language_function(self):
        """Test global detect_language function."""
        # English text
        result = detect_language("Hello world")
        assert result == "en"
        
        # Chinese text
        result = detect_language("你好世界")
        assert result == "zh"

    def test_detect_language_with_preference(self):
        """Test global detect_language with user preference."""
        result = detect_language("Hello world", user_preference="zh")
        assert result == "zh"

    def test_is_supported_language_function(self):
        """Test global is_supported_language function."""
        assert is_supported_language("en") == True
        assert is_supported_language("zh") == True
        assert is_supported_language("de") == False

    def test_get_supported_languages_function(self):
        """Test global get_supported_languages function."""
        languages = get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) == 5


class TestSupportedLanguage:
    """Test suite for SupportedLanguage enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert SupportedLanguage.ENGLISH.value == "en"
        assert SupportedLanguage.CHINESE.value == "zh"
        assert SupportedLanguage.JAPANESE.value == "ja"
        assert SupportedLanguage.SPANISH.value == "es"
        assert SupportedLanguage.FRENCH.value == "fr"

    def test_enum_from_value(self):
        """Test creating enum from value."""
        assert SupportedLanguage("en") == SupportedLanguage.ENGLISH
        assert SupportedLanguage("zh") == SupportedLanguage.CHINESE

    def test_enum_invalid_value(self):
        """Test creating enum from invalid value."""
        with pytest.raises(ValueError):
            SupportedLanguage("invalid")


class TestEdgeCases:
    """Test suite for edge cases and special scenarios."""

    def test_mixed_language_text(self):
        """Test detection with mixed language text."""
        detector = LanguageDetector()
        
        # English with some Chinese
        text = "Hello 世界 world"
        result = detector.detect_language(text)
        # Should prefer the language with more matches
        assert result in [SupportedLanguage.ENGLISH, SupportedLanguage.CHINESE]

    def test_numbers_and_symbols_only(self):
        """Test detection with only numbers and symbols."""
        detector = LanguageDetector()
        
        text = "123 456 !@# $%^"
        result = detector.detect_language(text)
        assert result == detector.default_language

    def test_very_short_text(self):
        """Test detection with very short text."""
        detector = LanguageDetector()
        
        # Single word
        assert detector.detect_language("hello") == SupportedLanguage.ENGLISH
        assert detector.detect_language("你好") == SupportedLanguage.CHINESE

    def test_very_long_text(self):
        """Test detection with very long text."""
        detector = LanguageDetector()
        
        # Long English text
        long_text = "Hello world. " * 1000
        result = detector.detect_language(long_text)
        assert result == SupportedLanguage.ENGLISH

    def test_special_characters(self):
        """Test detection with special characters."""
        detector = LanguageDetector()
        
        # English with special characters
        text = "Hello @user, check out https://example.com #test"
        result = detector.detect_language(text)
        assert result == SupportedLanguage.ENGLISH

    def test_code_snippets(self):
        """Test detection with code snippets."""
        detector = LanguageDetector()
        
        # Python code
        code = "def hello_world():\n    print('Hello, World!')\n    return True"
        result = detector.detect_language(code)
        # Should detect English due to keywords
        assert result == SupportedLanguage.ENGLISH


class TestGlobalDetectorInstance:
    """Test suite for global language_detector instance."""

    def test_global_instance_exists(self):
        """Test that global instance exists."""
        assert language_detector is not None
        assert isinstance(language_detector, LanguageDetector)

    def test_global_instance_default_language(self):
        """Test global instance default language."""
        assert language_detector.default_language == SupportedLanguage.ENGLISH

    def test_global_instance_usage(self):
        """Test using global instance."""
        result = language_detector.detect_language("Hello world")
        assert result == SupportedLanguage.ENGLISH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
