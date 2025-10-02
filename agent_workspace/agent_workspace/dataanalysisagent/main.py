import os
from dotenv import load_dotenv
import logging

# Load environment configuration
load_dotenv()

# Validate required configurations
REQUIRED_VARS = ["TAVILY_API_KEY"]
for var in REQUIRED_VARS:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    filename=os.getenv("LOG_FILE", "analysis_log.txt"),
    level=logging.getLevelName(LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Set up output directory
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Configure data source preference
DATA_SOURCE = os.getenv("DATA_SOURCE", "LOCAL")