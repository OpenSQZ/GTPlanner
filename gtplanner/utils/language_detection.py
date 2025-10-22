"""
Language detection and management utilities for GTPlanner.

This module provides functionality for:
- Automatic language detection from user input
- Language preference management
- Supported language validation
"""

import re
from typing import Optional, Dict, List
from enum import Enum


class SupportedLanguage(Enum):
    """Enumeration of supported languages."""
    ENGLISH = "en"
    CHINESE = "zh"
    SPANISH = "es"
    FRENCH = "fr"
    JAPANESE = "ja"


class LanguageDetector:
    """Language detection and management class."""
    
    # Language patterns for basic detection
    LANGUAGE_PATTERNS = {
        SupportedLanguage.CHINESE: [
            r'[\u4e00-\u9fff]',  # Chinese characters
            r'[\u3400-\u4dbf]',  # CJK Extension A
            r'[\uf900-\ufaff]',  # CJK Compatibility Ideographs
        ],
        SupportedLanguage.JAPANESE: [
            r'[\u3040-\u309f]',  # Hiragana
            r'[\u30a0-\u30ff]',  # Katakana
            r'[\u4e00-\u9fff]',  # Kanji (shared with Chinese)
        ],
        SupportedLanguage.SPANISH: [
            r'\b(el|la|los|las|un|una|de|del|en|con|por|para|que|es|son|está|están)\b',
            r'[ñáéíóúü]',  # Spanish specific characters
        ],
        SupportedLanguage.FRENCH: [
            r'\b(le|la|les|un|une|de|du|des|en|avec|pour|que|est|sont|être|avoir)\b',
            r'[àâäéèêëïîôöùûüÿç]',  # French specific characters
        ],
    }
    
    # Common English words for detection
    ENGLISH_PATTERNS = [
        r'\b(the|and|or|but|in|on|at|to|for|of|with|by|from|about|into|through|during|before|after|above|below|up|down|out|off|over|under|again|further|then|once)\b',
        r'\b(is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|could|should|may|might|can|must)\b',
    ]
    
    def __init__(self, default_language: SupportedLanguage = SupportedLanguage.ENGLISH):
        """Initialize the language detector.
        
        Args:
            default_language: The default language to use when detection fails
        """
        self.default_language = default_language
        
    def detect_language(self, text: str, user_preference: Optional[str] = None) -> SupportedLanguage:
        """Detect the language of the given text.
        
        Args:
            text: The text to analyze
            user_preference: User's preferred language code (e.g., 'en', 'zh')
            
        Returns:
            The detected or preferred language
        """
        # First, check if user has specified a preference
        if user_preference:
            try:
                return SupportedLanguage(user_preference.lower())
            except ValueError:
                pass  # Invalid preference, continue with detection
        
        if not text or not text.strip():
            return self.default_language
            
        text = text.lower()
        language_scores = {}
        
        # Score each language based on pattern matches
        for language, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            language_scores[language] = score
        
        # Check English patterns
        english_score = 0
        for pattern in self.ENGLISH_PATTERNS:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            english_score += matches
        language_scores[SupportedLanguage.ENGLISH] = english_score
        
        # Special handling for Chinese vs Japanese
        if (language_scores.get(SupportedLanguage.CHINESE, 0) > 0 and 
            language_scores.get(SupportedLanguage.JAPANESE, 0) > 0):
            # If both Chinese and Japanese patterns match, check for Japanese-specific patterns
            hiragana_matches = len(re.findall(r'[\u3040-\u309f]', text))
            katakana_matches = len(re.findall(r'[\u30a0-\u30ff]', text))
            
            if hiragana_matches > 0 or katakana_matches > 0:
                language_scores[SupportedLanguage.JAPANESE] += 10
            else:
                language_scores[SupportedLanguage.CHINESE] += 5
        
        # Return the language with the highest score
        if language_scores:
            detected_language = max(language_scores, key=language_scores.get)
            if language_scores[detected_language] > 0:
                return detected_language
        
        return self.default_language
    
    def is_supported_language(self, language_code: str) -> bool:
        """Check if a language code is supported.
        
        Args:
            language_code: The language code to check
            
        Returns:
            True if the language is supported, False otherwise
        """
        try:
            SupportedLanguage(language_code.lower())
            return True
        except ValueError:
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Get a list of all supported language codes.
        
        Returns:
            List of supported language codes
        """
        return [lang.value for lang in SupportedLanguage]
    
    def get_language_name(self, language_code: str) -> str:
        """Get the human-readable name of a language.
        
        Args:
            language_code: The language code
            
        Returns:
            The human-readable language name
        """
        language_names = {
            SupportedLanguage.ENGLISH.value: "English",
            SupportedLanguage.CHINESE.value: "中文",
            SupportedLanguage.SPANISH.value: "Español",
            SupportedLanguage.FRENCH.value: "Français",
            SupportedLanguage.JAPANESE.value: "日本語",
        }
        return language_names.get(language_code.lower(), "Unknown")


# Global language detector instance
language_detector = LanguageDetector()


def detect_language(text: str, user_preference: Optional[str] = None) -> str:
    """Convenience function for language detection.
    
    Args:
        text: The text to analyze
        user_preference: User's preferred language code
        
    Returns:
        The detected language code
    """
    return language_detector.detect_language(text, user_preference).value


def is_supported_language(language_code: str) -> bool:
    """Convenience function to check if a language is supported.
    
    Args:
        language_code: The language code to check
        
    Returns:
        True if supported, False otherwise
    """
    return language_detector.is_supported_language(language_code)


def get_supported_languages() -> List[str]:
    """Convenience function to get supported languages.
    
    Returns:
        List of supported language codes
    """
    return language_detector.get_supported_languages()
