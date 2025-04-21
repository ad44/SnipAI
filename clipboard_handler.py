"""
Clipboard handler module for the Contexta application.
Manages clipboard operations to capture selected text.
"""
import time
import logging
import keyboard
import pyperclip

# Configure logging
logger = logging.getLogger(__name__)

# Store original clipboard content
_original_clipboard = None

def _save_clipboard():
    """
    Saves the current clipboard content.
    Returns the content for verification purposes.
    """
    global _original_clipboard
    try:
        _original_clipboard = pyperclip.paste()
        logger.debug("Original clipboard content saved")
        return _original_clipboard
    except Exception as e:
        logger.error(f"Error saving clipboard content: {str(e)}")
        _original_clipboard = None
        return None

def _restore_clipboard():
    """Restores the previously saved clipboard content."""
    global _original_clipboard
    if _original_clipboard is not None:
        try:
            pyperclip.copy(_original_clipboard)
            logger.debug("Original clipboard content restored")
        except Exception as e:
            logger.error(f"Error restoring clipboard content: {str(e)}")
        _original_clipboard = None
    else:
        logger.debug("No original clipboard content to restore")

def get_selected_text_via_copy():
    """
    Gets the currently selected text using clipboard manipulation.
    Improved for compatibility with Microsoft Teams and other applications
    that may handle clipboard operations differently.
    
    Returns:
        str or None: The selected text or None if no text was selected.
    """
    global _original_clipboard
    selected_text = None
    
    try:
        # Save the original clipboard content
        original_content = _save_clipboard()
        logger.debug(f"Original clipboard content length: {len(original_content) if original_content else 0} characters")
        
        try:
            # Try multiple approaches to copy text, starting with the standard approach
            methods = [
                # Method 1: Standard Ctrl+C
                lambda: keyboard.press_and_release('ctrl+c'),
                
                # Method 2: Press and hold approach
                lambda: (keyboard.press('ctrl'), 
                         time.sleep(0.1), 
                         keyboard.press('c'), 
                         time.sleep(0.1), 
                         keyboard.release('c'), 
                         time.sleep(0.1),
                         keyboard.release('ctrl')),
                
                # Method 3: Teams-specific (Ctrl+C with longer delay)
                lambda: (keyboard.press_and_release('ctrl+c'),
                         time.sleep(0.5))  # Teams might need a longer delay
            ]
            
            # Try each method until we get something different from original clipboard
            for i, method in enumerate(methods):
                logger.debug(f"Trying copy method {i+1}")
                
                # Execute the copy method to replicate the data
                # Execute the copy method
                method()
                
                # Allow some time for the clipboard to update
                time.sleep(0.3)
                
                # Get clipboard content
                current_content = pyperclip.paste()
                
                # Check if we got some text and it's different from original
                if current_content and current_content != original_content:
                    selected_text = current_content
                    logger.info(f"Copy method {i+1} succeeded, got {len(selected_text)} characters")
                    break
            
            # If all methods failed, log it
            if selected_text is None:
                logger.info("All copy methods failed, no text was selected or app doesn't support clipboard copy")
                
        except Exception as e:
            logger.error(f"Error during copy simulation: {str(e)}")
            selected_text = None
            
    finally:
        # Always attempt to restore the original clipboard content
        _restore_clipboard()
        
    return selected_text

# Test function for when this module is run directly
def test_clipboard_handler():
    """
    Provides a menu-driven interface to test direct clipboard functions using pyperclip.
    Does not simulate key presses or use get_selected_text_via_copy.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting clipboard handler direct access test...")

    while True:
        print("\n--- Clipboard Direct Access Test Menu ---")
        print("1. View current clipboard content")
        print("2. Set clipboard content")
        print("3. Clear clipboard content")
        print("4. Exit")

        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            try:
                content = pyperclip.paste()
                print(f"\nCurrent clipboard content:\n---\n{content}\n---")
            except Exception as e:
                print(f"Error reading clipboard: {e}")
        
        elif choice == '2':
            new_content = input("Enter the text to set as clipboard content: ")
            try:
                pyperclip.copy(new_content)
                print("Clipboard content updated.")
            except Exception as e:
                print(f"Error setting clipboard content: {e}")

        elif choice == '3':
            try:
                pyperclip.copy('') # Set clipboard to empty string
                print("Clipboard content cleared.")
            except Exception as e:
                print(f"Error clearing clipboard content: {e}")

        elif choice == '4':
            print("Exiting clipboard test.")
            break
        
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    test_clipboard_handler()