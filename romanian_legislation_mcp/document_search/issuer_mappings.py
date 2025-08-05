ISSUER_MAPPINGS = {
    # ===== CENTRAL BANK =====
    "bnr": "banca nationala a romaniei",
    "banca nationala": "banca nationala a romaniei",
    "banca na?ionala a romaniei": "banca nationala a romaniei",
    
    # ===== GOVERNMENT & PARLIAMENT =====
    "guvern": "guvernul",
    "guvernul": "guvernul",
    "guvernul romaniei": "guvernul",
    "guvernul romaniei": "guvernul",
    "consiliul de mini?tri": "consiliul de ministri",
    "camera deputaților": "camera deputatilor",
    "camera deputa?ilor": "camera deputatilor",
    "senat": "senatul",
    "senatul romaniei": "senatul",
    
    # ===== TAX & FINANCIAL AUTHORITIES =====
    "anaf": "agentia nationala de administrare fiscala",
    "agen?ia na?ionala de administrare fiscala":"agentia nationala de administrare fiscala",
    "ministerul finan?elor": "ministerul finantelor",
    "ministerul finan?elor publice":"ministerul finantelor publice",
    
    # ===== MINISTRIES =====
    "ministerul agriculturii, padurilor ?i dezvoltarii rurale": "ministerul agriculturii, padurilor si dezvoltarii rurale",
    "ministerul agriculturii ?i dezvoltarii rurale":"ministerul agriculturii si dezvoltarii rurale",
    "ministerul agriculturii, alimenta?iei ?i padurilor": "ministerul agriculturii, alimentatiei si padurilor",
    "ministerul agriculturii, padurilor, apelor ?i mediului": "ministerul agriculturii, padurilor, apelor si mediului",
    "ministerul administra?iei ?i internelor":"ministerul administratiei si internelor",
    "ministerul culturii ?i cultelor": "ministerul culturii si cultelor",
    "ministerul industriei ?i resurselor": "ministerul industriei si resurselor",
    "ministerul sanata?ii": "ministerul sanatatii",
    "ministerul sanata?ii publice": "ministerul sanatatii publice",
    "ministerul sanata?ii ?i familiei": "ministerul sanatatii si familiei",
    "ministerul educa?iei": "ministerul educatiei",
    "ministerul educa?iei na?ionale": "ministerul educatiei nationale",
    "ministerul apararii na?ionale": "ministerul apararii nationale",
    "ministerul educa?iei ?i cercetarii": "ministerul educatiei si cercetarii",
    
    # ===== AGENCIES & AUTHORITIES =====
    "agen?ia na?ionala pentru resurse minerale":"agentia nationala pentru resurse minerale",
    "comisia na?ionala pentru contrololul activita?ilor nucleare":"comisia nationala pentru contrololul activitatilor nucleare",
    "autoritatea na?ionala sanitara veterinara ?i pentru siguran?a alimentelor":"autoritatea nationala sanitara veterinara si pentru siguranta alimentelor",
    "anpc": "autoritatea nationala pentru protectia consumatorilor",
    "autoritatea na?ionala pentru protec?ia consumatorilor": "autoritatea nationala pentru protectia consumatorilor",
    "autoritatea na?ionala de reglementare in domeniul energiei": "autoritatea nationala de reglementare in domeniul energiei",
    "consiliul na?ional al audiovizualului": "consiliul national al audiovizualului",
    
    # ===== PROFESSIONAL BODIES =====
    "colegiul fizioterapeu?ilor din romania": "colegiul fizioterapeutilor din romania",
    "ordinul arhitec?ilor din romania": "ordinul arhitectilor din romania",
    "camera consultan?ilor fiscali": "camera consultantilor fiscali",
    
    # ===== JUDICIAL & ELECTORAL =====
    "curtea constitu?ionala": "curtea constitutionala",
    "inalta curte de casa?ie ?i justi?ie": "inalta curte de casatie si justitie",
    "biroul electoral jude?ean": "biroul electoral judetean",
    
    # ===== STATISTICAL & RESEARCH =====
    "institutul na?ional de statistica (?i studii economice)": "institutul national de statistica (si studii economice)",
}


def get_canonical_issuer(issuer: str) -> str:
    """Get canonical form of issuer for comparison"""
    normalized = issuer.strip().lower()
    normalized = (
        normalized.replace("ă", "a")
        .replace("â", "a")
        .replace("î", "i")
        .replace("ț", "t")
        .replace("ţ", "t")
        .replace("ş", "s")
    )

    return ISSUER_MAPPINGS.get(normalized, normalized)
