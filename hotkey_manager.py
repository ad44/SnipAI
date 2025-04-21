"""
Hotkey manager module for the Contexta application.
Sets up the global hotkey listener with debouncing.
"""
import time
import logging
import keyboard
import threading

# Configure logging
logger = logging.getLogger(__name__)

# Flag to track if a hotkey was recently pressed
_hotkey_pressed = False
_debounce_time = 0.5  # 500ms debounce

def _reset_hotkey_flag():
    """Resets the hotkey pressed flag."""
    global _hotkey_pressed
    _hotkey_pressed = False

def _debounce_callback(callback_function):
    """
    Creates a debounced version of the callback function.
    Prevents multiple rapid firing of the callback if key is held down.
    """
    global _hotkey_pressed
    
    def debounced_function():
        global _hotkey_pressed
        if not _hotkey_pressed:
            _hotkey_pressed = True
            try:
                callback_function()
            except Exception as e:
                logger.error(f"Error in hotkey callback: {str(e)}")
            
            # Reset the flag after debounce time using a dedicated function
            threading.Timer(_debounce_time, _reset_hotkey_flag).start()
    
    return debounced_function

def setup_hotkey(hotkey_combination, callback_function):
    """
    Set up the global hotkey listener.
    
    Args:
        hotkey_combination (str): Keyboard combination to listen for (e.g., 'ctrl+alt+c').
        callback_function (callable): Function to call when hotkey is pressed.
    """
    # Create debounced version of the callback
    debounced_callback = _debounce_callback(callback_function)
    
    try:
        # Register the hotkey
        logger.info(f"Registering hotkey: {hotkey_combination}")
        keyboard.add_hotkey(hotkey_combination, debounced_callback)
        logger.info(f"Hotkey {hotkey_combination} registered successfully")
        
        # Keep the listener running
        logger.info("Hotkey listener started")
        keyboard.wait()
        
    except Exception as e:
        logger.error(f"Error setting up hotkey {hotkey_combination}: {str(e)}")
        if "KeyboardEvent" in str(e):
            logger.error("This could be due to permission issues or conflicts with existing hotkeys")
    
    finally:
        # Clean up
        logger.info("Cleaning up hotkey registrations")
        keyboard.unhook_all_hotkeys()