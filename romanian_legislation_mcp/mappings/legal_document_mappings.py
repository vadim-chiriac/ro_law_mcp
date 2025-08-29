"""
Legal document identification mappings for Romanian legislation.
Contains mappings from natural language descriptions to exact document parameters.
"""

BASE_DOCUMENTS = {
    "civil_code": {
        "document_type": "lege",
        "number": 287,
        "year": 2009,
        "issuer": "Parlamentul",
        "full_name": "LEGE nr. 287 din 17 iulie 2009 privind Codul civil",
    },
    "criminal_code": {
        "document_type": "lege",
        "number": 286,
        "year": 2009,
        "issuer": "Parlamentul",
        "full_name": "LEGE nr. 286 din 17 iulie 2009 privind Codul civil",
    },
    "labor_code": {
        "document_type": "lege",
        "number": 53,
        "year": 2003,
        "issuer": "Parlamentul",
        "full_name": "CODUL MUNCII din 24 ianuarie 2003",
    },
    "tax_code": {
        "document_type": "lege",
        "number": 227,
        "year": 2015,
        "issuer": "Parlamentul",
        "full_name": "LEGE nr. 227 din 8 septembrie 2015 privind Codul fiscal",
    },
    "civil_procedure_code": {
        "document_type": "lege",
        "number": 134,
        "year": 2010,
        "issuer": "Parlamentul",
        "full_name": "LEGE nr. 134 din 1 iulie 2010 privind Codul de procedură civilă",
    },
    "criminal_procedure_code": {
        "document_type": "lege",
        "number": 135,
        "year": 2010,
        "issuer": "Parlamentul",
        "full_name": "LEGE nr. 135 din 1 iulie 2010 privind Codul de procedură penală",
    },
    "tax_procedure_code": {
        "document_type": "lege",
        "number": 207,
        "year": 2015,
        "issuer": "Parlamentul",
        "full_name": "LEGE nr. 207 din 20 iulie 2015 privind Codul de procedură fiscală",
    },
}

DOCUMENT_MAPPINGS = {
    # Civil Code variations
    "civil code": BASE_DOCUMENTS["civil_code"],
    "codul civil": BASE_DOCUMENTS["civil_code"],
    "cc": BASE_DOCUMENTS["civil_code"],
    # Criminal Code variations
    "criminal code": BASE_DOCUMENTS["criminal_code"],
    "codul penal": BASE_DOCUMENTS["criminal_code"],
    "penal code": BASE_DOCUMENTS["criminal_code"],
    "cp": BASE_DOCUMENTS["criminal_code"],
    # Labor Code variations
    "labor code": BASE_DOCUMENTS["labor_code"],
    "labour code": BASE_DOCUMENTS["labor_code"],
    "codul muncii": BASE_DOCUMENTS["labor_code"],
    "cm": BASE_DOCUMENTS["labor_code"],
    # Tax/Fiscal Code variations
    "tax code": BASE_DOCUMENTS["tax_code"],
    "fiscal code": BASE_DOCUMENTS["tax_code"],
    "codul fiscal": BASE_DOCUMENTS["tax_code"],
    "cf": BASE_DOCUMENTS["tax_code"],
    # Civil Procedure Code variations
    "civil procedure code": BASE_DOCUMENTS["civil_procedure_code"],
    "code of civil procedure": BASE_DOCUMENTS["civil_procedure_code"],
    "codul de procedura civila": BASE_DOCUMENTS["civil_procedure_code"],
    "cpc": BASE_DOCUMENTS["civil_procedure_code"],
    # Criminal Procedure Code variations
    "criminal procedure code": BASE_DOCUMENTS["criminal_procedure_code"],
    "code of criminal procedure": BASE_DOCUMENTS["criminal_procedure_code"],
    "codul de procedura penala": BASE_DOCUMENTS["criminal_procedure_code"],
    "cpp": BASE_DOCUMENTS["criminal_procedure_code"],
    # Tax Procedure Code variations
    "tax procedure code": BASE_DOCUMENTS["tax_procedure_code"],
    "fiscal procedure code": BASE_DOCUMENTS["tax_procedure_code"],
    "codul de procedura fiscala": BASE_DOCUMENTS["tax_procedure_code"],
    "cpf": BASE_DOCUMENTS["tax_procedure_code"],
}

COMMON_DOCUMENTS = [
    {"name": "Civil Code (Codul Civil)", "search_hint": "codul civil"},
    {"name": "Criminal Code (Codul Penal)", "search_hint": "codul penal"},
    {"name": "Labor Code (Codul Muncii)", "search_hint": "codul muncii"},
    {"name": "Tax Code (Codul Fiscal)", "search_hint": "codul fiscal"},
    {
        "name": "Civil Procedure Code (Codul de Procedura Civila)",
        "search_hint": "codul de procedura civila",
    },
    {
        "name": "Criminal Procedure Code (Codul de Procedura Penala)",
        "search_hint": "codul de procedura penala",
    },
    {
        "name": "Tax Procedure Code (Codul de Procedura Fiscala)",
        "search_hint": "codul de procedura fiscala",
    },
]

ISSUER_MAPPINGS_FOR_TOOLS = {
    # Government variations
    "government": "Guvernul",
    "guvern": "Guvernul",
    "guvernul": "Guvernul",
    "guvernul romaniei": "Guvernul",
    "government of romania": "Guvernul",
    "romanian government": "Guvernul",
    # Parliament variations
    "parliament": "Parlamentul",
    "parlamentul": "Parlamentul",
    "parlament": "Parlamentul",
    "parlamentul romaniei": "Parlamentul",
    "parliament of romania": "Parlamentul",
    "romanian parliament": "Parlamentul",
    # Prime Minister variations
    "prime minister": "Prim-ministrul",
    "prim ministru": "Prim-ministrul",
    "primul ministru": "Prim-ministrul",
    "prim-ministru": "Prim-ministrul",
    "prim-ministrul": "Prim-ministrul",
    "pm": "Prim-ministrul",
    # President variations
    "president": "Presedintele Romaniei",
    "presedinte": "Presedintele Romaniei",
    "presedintele": "Presedintele Romaniei",
    "presedintele romaniei": "Presedintele Romaniei",
    "president of romania": "Presedintele Romaniei",
    # Ministries (common ones)
    "ministry of finance": "Ministerul Finantelor",
    "ministerul finantelor": "Ministerul Finantelor",
    "ministry of health": "Ministerul Sanatatii",
    "ministerul sanatatii": "Ministerul Sanatatii",
    "ministry of education": "Ministerul Educatiei",
    "ministerul educatiei": "Ministerul Educatiei",
    "ministry of interior": "Ministerul Afacerilor Interne",
    "ministerul afacerilor interne": "Ministerul Afacerilor Interne",
    "ministry of justice": "Ministerul Justitiei",
    "ministerul justitiei": "Ministerul Justitiei",
    # Agencies and authorities
    "anaf": "Agentia Nationala de Administrare Fiscala",
    "tax authority": "Agentia Nationala de Administrare Fiscala",
    "national bank": "Banca Nationala a Romaniei",
    "bnr": "Banca Nationala a Romaniei",
    "banca nationala": "Banca Nationala a Romaniei",
    # Consumer protection
    "anpc": "Autoritatea Nationala pentru Protectia Consumatorilor",
    "consumer protection": "Autoritatea Nationala pentru Protectia Consumatorilor",
    # Courts
    "constitutional court": "Curtea Constitutionala",
    "curtea constitutionala": "Curtea Constitutionala",
    "ccr": "Curtea Constitutionala",
    "supreme court": "Inalta Curte de Casatie si Justitie",
    "curtea suprema": "Inalta Curte de Casatie si Justitie",
    "inalta curte": "Inalta Curte de Casatie si Justitie",
    "iccj": "Inalta Curte de Casatie si Justitie",
}

COMMON_ISSUERS = [
    {"description": "Government/Executive", "issuer": "Guvernul"},
    {"description": "Parliament/Legislative", "issuer": "Parlamentul"},
    {"description": "Prime Minister", "issuer": "Prim-ministrul"},
    {"description": "President", "issuer": "Presedintele Romaniei"},
    {"description": "Ministry of Finance", "issuer": "Ministerul Finantelor"},
    {"description": "National Bank", "issuer": "Banca Nationala a Romaniei"},
]
