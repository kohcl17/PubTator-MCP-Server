ENTRY_URL='https://www.ncbi.nlm.nih.gov/research/pubtator3-api'

ENTITIES = [
    'gene',
    'chemical',
    'drugs',
    'disease',
    'variant',
    'species',
    'cell_line'
    ]

ENTITY_TYPES = [
    'gene',
    'chemical',
    'disease',
    'variant'
    ]

RELATION = [
    'associate',
    'cause',
    'compare',
    'cotreat',
    'drug_interact',
    'inhibit',
    'interact',
    'negative_correlate',
    'positive_correlate',
    'prevent',
    'stimulate',
    'treat'
]

AVAILABLE_FORMATS=["pubtator", "biocxml", "biocjson"]
PUB_ID_FORMATS=['pmid', 'pmcid']

FORMAT="pubtator"

headers = {"User-Agent": "Pubtator3 Python API",
            "Accept": "application/json"
            }