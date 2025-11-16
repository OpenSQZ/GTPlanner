# coding:utf-8
from typing import Dict, Optional

from .rag_doc_qa import RAG_DOC_QA_PROMPT


_PRESET_REGISTRY: Dict[str, Dict[str, str]] = {
    "rag-doc-qa": {
        "name": "rag-doc-qa",
        "prompt": RAG_DOC_QA_PROMPT,
        "description": "Document QA / standard-compliance RAG playbook",
    },
}


def available_presets() -> Dict[str, str]:
    """Return available preset names mapped to short descriptions."""
    return {name: meta["description"] for name, meta in _PRESET_REGISTRY.items()}


def get_preset_prompt(preset: Optional[str], language: Optional[str] = None) -> Optional[str]:
    """
    Resolve a preset prompt by name.

    Args:
        preset: Preset key from CLI or API.
        language: Currently unused, reserved for future localized presets.

    Returns:
        Preset prompt text or None when not found / default.
    """
    if not preset or preset == "default":
        return None

    meta = _PRESET_REGISTRY.get(preset)
    if not meta:
        return None

    return meta["prompt"]

