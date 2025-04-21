"""
Configuration module for the Contexta application.
Loads and provides configuration values.
"""
import os
import logging
import sys
import json  # Import json module

# Determine application path
if getattr(sys, 'frozen', False):
    # Executable mode
    application_path = os.path.dirname(sys.executable)
elif __file__:
    # Script mode
    application_path = os.path.dirname(__file__)
else:
    # Fallback (e.g., interactive mode)
    application_path = os.getcwd()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Log to console initially
)
logger = logging.getLogger(__name__)

# --- Configuration Loading Logic ---
_config_cache = None  # Initialize as None to indicate not loaded
_config_loaded_successfully = False

CONFIG_FILENAME = "config.json"
EXPECTED_KEYS = ["GROQ_API_KEY", "SNIPAI_HOTKEY"]

def _load_config():
    """
    Loads configuration strictly from config.json.
    Returns True if successful, False otherwise.
    Populates _config_cache on success.
    """
    global _config_cache, _config_loaded_successfully
    if _config_loaded_successfully:  # If already loaded successfully, return True
        return True
    if _config_cache is not False:  # If loading hasn't failed definitively yet
        config_file_path = os.path.join(application_path, CONFIG_FILENAME)
        logger.info(f"Attempting to load configuration from: {config_file_path}")

        try:
            with open(config_file_path, 'r') as f:
                _config_cache = json.load(f)
            logger.info(f"Successfully loaded configuration from {config_file_path}")

            # Validate essential keys
            missing_keys = [key for key in EXPECTED_KEYS if key not in _config_cache or not _config_cache[key]]
            if missing_keys:
                logger.error(f"Missing or empty essential keys in {config_file_path}: {', '.join(missing_keys)}")
                _config_cache = False  # Mark loading as failed
                return False

            _config_loaded_successfully = True
            return True

        except FileNotFoundError:
            logger.error(f"CRITICAL: Configuration file '{config_file_path}' not found.")
            logger.error(f"Please create '{CONFIG_FILENAME}' in the application directory with keys: {', '.join(EXPECTED_KEYS)}")
            _config_cache = False  # Mark loading as failed
            return False
        except json.JSONDecodeError as e:
            logger.error(f"CRITICAL: Error decoding JSON from {config_file_path}: {e}")
            logger.error(f"Please ensure '{CONFIG_FILENAME}' is valid JSON.")
            _config_cache = False  # Mark loading as failed
            return False
        except Exception as e:
            logger.error(f"CRITICAL: Unexpected error loading {config_file_path}: {e}")
            _config_cache = False  # Mark loading as failed
            return False
    else:  # Loading previously failed
        return False

# --- Accessor Functions ---

def get_groq_api_key():
    """Get the Groq API key from the loaded configuration."""
    if not _load_config():
        raise ValueError(f"Configuration '{CONFIG_FILENAME}' is missing or invalid. Cannot retrieve GROQ_API_KEY.")

    api_key = _config_cache.get("GROQ_API_KEY")
    if not api_key:  # Should be caught by _load_config, but double-check
        raise ValueError(f"GROQ_API_KEY is missing or empty in '{CONFIG_FILENAME}'.")
    return api_key

def get_hotkey():
    """Get the hotkey combination from the loaded configuration."""
    if not _load_config():
        raise ValueError(f"Configuration '{CONFIG_FILENAME}' is missing or invalid. Cannot retrieve SNIPAI_HOTKEY.")

    hotkey = _config_cache.get("SNIPAI_HOTKEY")
    if not hotkey:  # Should be caught by _load_config, but double-check
        raise ValueError(f"SNIPAI_HOTKEY is missing or empty in '{CONFIG_FILENAME}'.")
    logger.info(f"Using hotkey: {hotkey}")
    return hotkey

# --- Other Config Functions ---

def get_llm_model_name():
    """Returns the Groq model name."""
    return "llama-3.3-70b-versatile"

def get_system_prompt():
    """Returns the default system prompt for the LLM."""
    return """You are SnipAI, a helpful AI assistant that provides concise, clear, and accurate responses to user inquiries based on the provided text.
When analyzing text, focus on the most relevant points and provide insightful observations.
If you're unsure about something, acknowledge it rather than making assumptions.

IMPORTANT: If your response involves providing a modified, translated, summarized, corrected, or otherwise altered version of the original text provided by the user:
1. You MUST provide this altered text exclusively within a specific JSON format.
2. Use the following structure exactly: ```json {{"enhanced_content": "Your altered text here"}}```
3. Any explanation or commentary about the changes should be provided as regular text *outside* the JSON block. Do NOT include explanations inside the JSON.

Example of a proper response when providing altered text (e.g., translation):
"Here is the Hindi translation:

```json
{{"enhanced_content": "यहाँ हिंदी अनुवाद है।"}}
```

This translates the original English sentence into Hindi."

If you are only answering a question about the text or providing commentary *without* altering the original text itself, do NOT use the JSON format.
"""

def get_initial_user_prompt_template():
    """Returns the template for the first user message."""
    return """Selected text:
```
{selected_text}
```
Please analyze or respond to the above text."""