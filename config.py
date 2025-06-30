import os
from dotenv import load_dotenv
from typing import Optional

class ConfigError(Exception):
    """Configuration error class"""
    pass

def get_env_var(name: str, default: Optional[str] = None) -> str:
    """
    Get environment variable with error handling.
    If default is None and variable is not set, raises ConfigError.
    """
    value = os.getenv(name) # Do not pass default directly to os.getenv if we want to raise error on None
    if value is None:
        if default is not None:
            return default # Return default if provided and env var not set
        raise ConfigError(f"Required environment variable {name} is not set.")
    return value

# Load .env file
# It's good practice to ensure it loads at the very beginning
if not load_dotenv():
    print("Warning: Could not load .env file - ensure it exists and is correctly configured.")

# API Configuration
try:
    # Required configuration
    GOOGLE_CSE_ID = get_env_var("GOOGLE_CSE_ID")
    GOOGLE_API_KEY = get_env_var("GOOGLE_API_KEY")
    
    # API keys for language models.
    # It's good to be explicit about which one is primarily used or if both are optional.
    # Assuming OPENROUTER_API_KEY is the one truly used for your LLM calls.
    OPENROUTER_API_KEY = get_env_var("OPENROUTER_API_KEY") 
    
    # If you intend to use OpenAI directly, uncomment and ensure it's distinct in .env
    # OPENAI_API_KEY = get_env_var("OPENAI_API_KEY", default="") 
    
    # Search settings
    MAX_SEARCH_RESULTS = int(get_env_var("MAX_SEARCH_RESULTS", "5")) # Default should match .env or common sense
    SEARCH_TIMEOUT = int(get_env_var("SEARCH_TIMEOUT", "15"))
    
    # Cache settings
    ENABLE_CACHE = get_env_var("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL = int(get_env_var("CACHE_TTL", "3600"))  # 1 hour
    
except ConfigError as e:
    print(f"FATAL Configuration Error: {e}")
    # It's better to exit cleanly if critical environment variables are missing
    # or if you want to prevent the application from running incomplete.
    exit(1) # Exit with an error code

# You can add a print statement to confirm loaded values (for debugging, remove in production)
# print(f"Loaded Config: CSE_ID={GOOGLE_CSE_ID}, API_KEY_PREFIX={GOOGLE_API_KEY[:5]}..., "
#       f"OPENROUTER_KEY_PREFIX={OPENROUTER_API_KEY[:5]}..., MAX_SEARCH={MAX_SEARCH_RESULTS}")