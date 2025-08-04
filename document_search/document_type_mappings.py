import logging

logger = logging.getLogger(__name__)

SIMPLE_TYPE_MAPPINGS = {
    "lege": "lege",
    "hotarare de guvern": "hg",
    "ordonanta de urgenta": "oug",
    "ordonanta urgenta": "oug",
    "ordonanta": "og",
    "ordonan?a": "og",
    "ordonan?a de urgen?a": "oug",
    "conven?ie":"conventie"
}

# Context-dependent mappings
CONTEXT_DEPENDENT_MAPPINGS = {
    ("hotarare", "guvernul"): "hg",
    ("hotarare", "camera_deputatilor"): "hotarare_camera",
    ("hotarare", "senat"): "hotarare_senat",
}


def get_canonical_document_type(doc_type: str, issuer_canonical: str) -> str:
    """Get canonical document type, considering issuer context"""
    
    normalized = doc_type.strip().lower()
    normalized = (
        normalized.replace("ă", "a")
        .replace("â", "a")
        .replace("ț", "t")
        .replace("ţ", "t")
        .replace("ş", "s")
    )

    context_key = (normalized, issuer_canonical)
    if context_key in CONTEXT_DEPENDENT_MAPPINGS:
        return CONTEXT_DEPENDENT_MAPPINGS[context_key]

    return SIMPLE_TYPE_MAPPINGS.get(normalized, normalized)
