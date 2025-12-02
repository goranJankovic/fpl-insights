from pathlib import Path

# Root directory
ROOT_DIR = Path(__file__).resolve().parent

DB_PATH = ROOT_DIR / "fpl.db"

# Default Monte Carlo simulations
DEFAULT_SIMS = 10000

# Default number of history games to calculate variance
DEFAULT_HISTORY_GW = 5

