import os

from dotenv import load_dotenv

load_dotenv()

ENGINE = os.getenv("ENGINE", "duckdb")          # "duckdb" (local, no cloud) or "bigquery"
GCP_PROJECT = os.getenv("GCP_PROJECT", "")
BQ_DATASET = os.getenv("BQ_DATASET", "mandi")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/pipeline.duckdb")

RAW_CSV = os.getenv("RAW_CSV", "data/raw/agmarknet.csv")
CHUNK_ROWS = 500_000

# SCOPE. Fill these in AFTER running scripts.profile_csv. Names match case-insensitively.
COMMODITIES = ["onion", "tomato", "potato"]      # start with 3, grow to 6-8
STATES = []                                      # empty list = all states

# Units you accept, after you have seen the profile output. Case-insensitive.
PRICE_UNITS_OK = {"rs/quintal"}
ARRIVALS_TO_TONNES = {"tonnes": 1.0, "tonne": 1.0, "quintal": 0.1, "quintals": 0.1}

MAX_PRICE = 100_000        # Rs per quintal; above this a row is rejected as an obvious error
MIN_MARKETS = 5            # a daily benchmark needs at least this many reporting markets
# A market-day is suspect if its price is outside this band of the SAME DAY's median across
# markets. (Real spikes hit many markets at once, so they are not flagged.)
OUTLIER_LOW, OUTLIER_HIGH = 0.25, 4.0
