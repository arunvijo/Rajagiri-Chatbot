import os
from dotenv import load_dotenv
from typing import Optional

class ConfigError(Exception):
    """Configuration error class"""
    pass

def get_env_var(name: str, default: Optional[str] = None) -> str:
    """
    Get environment variable with error handling
    """
    value = os.getenv(name, default)
    if value is None:
        raise ConfigError(f"Required environment variable {name} is not set")
    return value

# Load .env file
if not load_dotenv():
    print("Warning: Could not load .env file - using system environment variables")

# API Configuration
try:
    # Required configuration
    GOOGLE_CSE_ID = get_env_var("GOOGLE_CSE_ID")
    GOOGLE_API_KEY = get_env_var("GOOGLE_API_KEY")
    
    # Optional configuration with defaults
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    
    # Search settings
    MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "3"))
    SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", "15"))
    
    # Cache settings
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    
except ConfigError as e:
    print(f"Configuration error: {e}")
    raise