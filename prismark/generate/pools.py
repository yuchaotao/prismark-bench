"""Value pools for synthetic data.

All values are fictional. Numbers use reserved or test ranges where one exists
(555-01xx phone numbers, documentation IP blocks, test card prefixes).
"""

FIRST_NAMES = [
    "Avery", "Jordan", "Priya", "Mateo", "Hana", "Olusegun", "Clara", "Dmitri",
    "Leilani", "Tomasz", "Ngozi", "Rafael", "Ingrid", "Kenji", "Fatima", "Elliot",
    "Marisol", "Bao", "Siobhan", "Arjun", "Yasmin", "Callum", "Esperanza", "Wen",
]

LAST_NAMES = [
    "Okafor", "Lindqvist", "Ramanathan", "Delacroix", "Nakamura", "Brennan",
    "Castellano", "Haddad", "Kowalczyk", "Abernathy", "Moreau", "Oyelaran",
    "Thorsen", "Valdivia", "Whitlock", "Szabo", "Iyer", "Fairbanks", "Quintero",
    "Hargrove", "Petrakis", "Mbeki", "Sorensen", "Achterberg",
]

EMAIL_DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "proton.me", "fastmail.com", "icloud.com"]

STREETS = [
    "Maple Avenue", "Birchwood Lane", "Harbor Street", "Juniper Court", "Old Mill Road",
    "Cedar Ridge Drive", "Lakeview Terrace", "Foxglove Way", "Granite Boulevard",
]

CITIES = [
    ("Springfield", "IL", "627"), ("Bellevue", "WA", "980"), ("Asheville", "NC", "288"),
    ("Boulder", "CO", "803"), ("Savannah", "GA", "314"), ("Madison", "WI", "537"),
    ("Tucson", "AZ", "857"), ("Burlington", "VT", "054"), ("Eugene", "OR", "974"),
]

EMPLOYERS = [
    "Northwind Logistics", "Bluefin Analytics", "Cobalt Ridge Credit Union",
    "Harborview Dental Group", "Tallgrass Robotics", "Meridian Home Health",
    "Quillfeather Publishing", "Ironbark Construction",
]

JOB_TITLES = [
    "senior payroll specialist", "night-shift charge nurse", "warehouse supervisor",
    "staff data engineer", "claims adjuster", "middle school science teacher",
    "regional sales manager", "dental hygienist",
]

HEALTH_CONDITIONS = [
    "type 2 diabetes", "major depressive disorder", "HIV", "early-onset Alzheimer's disease",
    "bipolar II disorder", "stage 3 breast cancer", "epilepsy", "opioid use disorder",
    "an eating disorder", "multiple sclerosis",
]

MEDICATIONS = ["sertraline", "metformin", "lithium carbonate", "buprenorphine", "levetiracetam"]

RELIGIONS = ["practicing Muslim", "Jehovah's Witness", "Orthodox Jew", "Sikh", "Mormon", "Buddhist"]

ORIENTATIONS = ["gay", "lesbian", "bisexual", "asexual", "pansexual"]

POLITICAL = [
    "a registered Green Party member", "a local Democratic Socialists organizer",
    "a precinct captain for the county Republican Party", "a Libertarian Party volunteer",
]

ETHNICITIES = ["Hmong", "Roma", "Somali", "Navajo", "Kurdish", "Afro-Caribbean"]

CRIMINAL = [
    "a 2019 DUI conviction", "an arrest for shoplifting in 2021", "a felony drug possession charge",
    "a sealed juvenile assault record", "two years of probation for fraud",
]

INDIRECT = [
    "the only pediatric neurosurgeon at Riverside General",
    "the youngest partner ever promoted at Hale & Whitcombe",
    "the woman who won the 2024 Lakewood marathon in a wheelchair",
    "the night janitor on the fourth floor of our building",
    "my neighbor's eldest son who just got back from deployment",
    "the only Portuguese-speaking teacher at Elmwood Elementary",
]

# --- Hard negatives -------------------------------------------------------

PUBLIC_FIGURES = [
    "Abraham Lincoln", "Marie Curie", "Ada Lovelace", "Nelson Mandela",
    "Frida Kahlo", "Albert Einstein", "Rosalind Franklin", "Martin Luther King Jr.",
]

ORGANIZATIONS = [
    "the World Health Organization", "the Red Cross", "NASA", "the Federal Reserve",
    "the Smithsonian Institution", "UNICEF",
]

PLACES = ["the Grand Canyon", "Lake Superior", "Yellowstone", "the Mississippi River", "Mount Rainier"]

GENERIC_ROLES = ["a pharmacist", "the on-call engineer", "our account manager", "a customer", "the landlord"]
