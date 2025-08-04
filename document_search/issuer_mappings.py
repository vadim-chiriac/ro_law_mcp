ISSUER_MAPPINGS = {
    "bnr": "banca nationala a romaniei",
    "banca nationala": "banca nationala a romaniei",
    "guvern": "guvernul",
    "guvernul": "guvernul",
    "guvernul romaniei": "guvernul",
    "guvernul româniei": "guvernul",
    "camera deputatilor": "camera_deputatilor",
    "camera deputaților": "camera_deputatilor",
    "senat": "senat",
    "senatul": "senat",
    "senatul romaniei": "senat",
    "anaf": "agentia nationala de administrare fiscala",
    "ministerul finantelor": "ministerul finantelor publice",
    "ministerul finan?elor": "ministerul finantelor publice",
    "ministerul agriculturii, padurilor ?i dezvoltarii rurale": "ministerul agriculturii, padurilor si dezvoltarii rurale",
    "ministerul agriculturii ?i dezvoltarii rurale":"ministerul agriculturii si dezvoltarii rurale",
    "ministerul administra?iei ?i internelor":"ministerul administratiei si internelor",
    "agen?ia na?ionala pentru resurse minerale":"agentia nationala pentru resurse minerale",
    "comisia na?ionala pentru contrololul activita?ilor nucleare":"comisia nationala pentru contrololul activitatilor nucleare",
    "autoritatea na?ionala sanitara veterinara ?i pentru siguran?a alimentelor":"autoritatea nationala sanitara veterinara si pentru siguranta alimentelor"
}


def get_canonical_issuer(issuer: str) -> str:
    """Get canonical form of issuer for comparison"""
    normalized = issuer.strip().lower()
    normalized = (
        normalized.replace("ă", "a")
        .replace("â", "a")
        .replace("ț", "t")
        .replace("ţ", "t")
        .replace("ş", "s")
    )

    return ISSUER_MAPPINGS.get(normalized, normalized)
