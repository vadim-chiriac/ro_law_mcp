ISSUER_MAPPINGS = {
    "bnr": "bnr",
    "banca nationala a romaniei": "bnr", 
    "banca nationala": "bnr",
    
    "guvernul": "guvernul",
    "guvernul romaniei": "guvernul",
    "guvernul româniei": "guvernul",
    
    "camera deputatilor": "camera_deputatilor",
    "camera deputaților": "camera_deputatilor", 
    "senat": "senat",
    "senatul": "senat",
    "senatul romaniei": "senat",
    
    "anaf": "anaf",
    "agentia nationala de administrare fiscala": "anaf",
}

def get_canonical_issuer(issuer: str) -> str:
    """Get canonical form of issuer for comparison"""
    normalized = issuer.strip().lower()
    normalized = (
        normalized.replace("ă", "a").replace("â", "a")
        .replace("ț", "t").replace("ş", "s")
    )
    
    return ISSUER_MAPPINGS.get(normalized, normalized)