"""
Multilingual utilities for GTPlanner.

This module provides comprehensive utilities for handling multilingual
functionality including language detection, prompt selection, and
configuration management.
"""

from typing import Optional, Dict, Any, Tuple
import logging

from utils.language_detection import (
    SupportedLanguage, 
    LanguageDetector, 
    detect_language, 
    is_supported_language,
    get_supported_languages
)
from utils.prompt_templates import (
    PromptType, 
    get_prompt_template, 
    get_prompt_template_by_code
)

logger = logging.getLogger(__name__)


class MultilingualManager:
    """Central manager for multilingual functionality."""
    
    def __init__(self, default_language: str = "en"):
        """Initialize the multilingual manager.
        
        Args:
            default_language: Default language code to use
        """
        self.default_language = default_language
        self.language_detector = LanguageDetector(
            default_language=SupportedLanguage(default_language)
        )
    
    def determine_language(
        self, 
        user_input: str = "", 
        user_preference: Optional[str] = None,
        request_language: Optional[str] = None
    ) -> str:
        """Determine the best language to use based on multiple inputs.
        
        Priority order:
        1. Explicit request language parameter
        2. User preference setting
        3. Automatic detection from user input
        4. Default language
        
        Args:
            user_input: The user's input text for language detection
            user_preference: User's stored language preference
            request_language: Explicitly requested language for this request
            
        Returns:
            The determined language code
        """
        # Priority 1: Explicit request language
        if request_language:
            if is_supported_language(request_language):
                logger.info(f"Using explicit request language: {request_language}")
                return request_language.lower()
            else:
                logger.warning(f"Request language {request_language} is not supported")
        
        # Priority 2: User preference
        if user_preference and is_supported_language(user_preference):
            logger.info(f"Using user preference language: {user_preference}")
            return user_preference.lower()
        
        # Priority 3: Auto-detection from input
        if user_input and user_input.strip():
            detected = detect_language(user_input)
            logger.info(f"Detected language from input: {detected}")
            return detected
        
        # Priority 4: Default language
        logger.info(f"Using default language: {self.default_language}")
        return self.default_language
    
    def get_localized_prompt(
        self, 
        prompt_type: str, 
        language_code: str, 
        **kwargs
    ) -> str:
        """Get a localized prompt template with fallback support.
        
        Args:
            prompt_type: The type of prompt (e.g., 'generate_steps')
            language_code: The target language code
            **kwargs: Variables to format into the prompt template
            
        Returns:
            The formatted prompt template
        """
        try:
            # Get the template
            template = get_prompt_template_by_code(prompt_type, language_code)

            # Format the template with provided variables
            if kwargs:
                formatted_prompt = template.format(**kwargs)
            else:
                formatted_prompt = template

            logger.info(f"Retrieved {prompt_type} prompt in {language_code}")
            return formatted_prompt
            
        except ValueError as e:
            logger.warning(f"Failed to get prompt {prompt_type} in {language_code}: {e}")
            
            # Fallback to default language
            try:
                template = get_prompt_template_by_code(prompt_type, self.default_language)
                if kwargs:
                    formatted_prompt = template.format(**kwargs)
                else:
                    formatted_prompt = template
                
                logger.info(f"Using fallback prompt {prompt_type} in {self.default_language}")
                return formatted_prompt
                
            except ValueError as fallback_error:
                logger.error(f"Failed to get fallback prompt: {fallback_error}")
                raise ValueError(f"No prompt template available for {prompt_type}")
    
    def validate_language_request(self, language_code: Optional[str]) -> Tuple[bool, str]:
        """Validate a language request.
        
        Args:
            language_code: The language code to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not language_code:
            return True, "No language specified"
        
        if is_supported_language(language_code):
            return True, f"Language {language_code} is supported"
        
        supported = get_supported_languages()
        return False, f"Language {language_code} is not supported. Supported languages: {', '.join(supported)}"
    
    def get_language_info(self) -> Dict[str, Any]:
        """Get information about supported languages.
        
        Returns:
            Dictionary with language information
        """
        from utils.language_detection import language_detector
        
        supported_languages = get_supported_languages()
        language_info = {}
        
        for lang_code in supported_languages:
            language_info[lang_code] = {
                "code": lang_code,
                "name": language_detector.get_language_name(lang_code),
                "is_default": lang_code == self.default_language
            }
        
        return {
            "default_language": self.default_language,
            "supported_languages": language_info,
            "total_supported": len(supported_languages)
        }
    
    def create_multilingual_response(
        self, 
        content: str, 
        language_code: str,
        include_language_info: bool = False
    ) -> Dict[str, Any]:
        """Create a standardized multilingual response.
        
        Args:
            content: The main response content
            language_code: The language used for the response
            include_language_info: Whether to include language metadata
            
        Returns:
            Standardized response dictionary
        """
        response = {
            "content": content,
            "language": language_code,
            "timestamp": None  # Can be added if needed
        }
        
        if include_language_info:
            response["language_info"] = self.get_language_info()
        
        return response


# Global multilingual manager instance
multilingual_manager = MultilingualManager()


def determine_language(
    user_input: str = "", 
    user_preference: Optional[str] = None,
    request_language: Optional[str] = None
) -> str:
    """Convenience function to determine the best language to use.
    
    Args:
        user_input: The user's input text for language detection
        user_preference: User's stored language preference
        request_language: Explicitly requested language for this request
        
    Returns:
        The determined language code
    """
    return multilingual_manager.determine_language(
        user_input, user_preference, request_language
    )


def get_localized_prompt(prompt_type: str, language_code: str, **kwargs) -> str:
    """Convenience function to get a localized prompt.
    
    Args:
        prompt_type: The type of prompt (e.g., 'generate_steps')
        language_code: The target language code
        **kwargs: Variables to format into the prompt template
        
    Returns:
        The formatted prompt template
    """
    return multilingual_manager.get_localized_prompt(prompt_type, language_code, **kwargs)


def validate_language_request(language_code: Optional[str]) -> Tuple[bool, str]:
    """Convenience function to validate a language request.
    
    Args:
        language_code: The language code to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    return multilingual_manager.validate_language_request(language_code)


def get_language_info() -> Dict[str, Any]:
    """Convenience function to get language information.
    
    Returns:
        Dictionary with language information
    """
    return multilingual_manager.get_language_info()
