"""
Main module for the SnipAI application.
Initializes the application and starts the hotkey listener.
"""
import os
import logging
import threading
import customtkinter as ctk
import pyautogui
import pygetwindow as gw  # Import pygetwindow for window management
import sys  # Add sys import
from datetime import datetime  # Import datetime
import tkinter.messagebox as messagebox  # Import messagebox

from llm_service import GroqLLMService
import hotkey_manager
import clipboard_handler
import config
from chat_window import ChatWindow

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

# Set up Logging
def setup_logging():
    """Configures logging to write to a timestamped file in a 'logs' directory."""
    logs_dir = os.path.join(application_path, 'logs')
    try:
        os.makedirs(logs_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f'snipai_log_{timestamp}.log'
        log_file_path = os.path.join(logs_dir, log_filename)

        # Remove existing handlers and configure new ones
        root_logger = logging.getLogger()
        # Clear existing handlers
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),  # Keep console output
                logging.FileHandler(log_file_path)  # Add file handler
            ]
        )
        logging.info(f"Logging initialized. Log file: {log_file_path}")

    except Exception as e:
        # Fallback basic config if directory creation/file handling fails
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        logging.error(f"Failed to set up file logging: {e}. Logging to console only.")

# Call logging setup immediately
setup_logging()
logger = logging.getLogger(__name__)  # Get logger instance after setup

# Global variables
llm_service = None
root = None

def trigger_chat_popup():
    """
    Callback function for hotkey press.
    Captures selected text and opens a chat window.
    """
    global llm_service, root
    
    try:
        # Get the active window before any operations
        try:
            active_window = gw.getActiveWindow()
            window_title = active_window.title if active_window else "Unknown"
            logger.info(f"Active window when hotkey triggered: {window_title}")
        except Exception as e:
            logger.error(f"Error getting active window: {str(e)}")
            active_window = None
        
        # Capture the selected text
        selected_text = clipboard_handler.get_selected_text_via_copy()
        
        if selected_text:
            logger.info(f"Selected text captured: {len(selected_text)} characters")
            
            # Get the current cursor position
            mouse_x, mouse_y = pyautogui.position()
            logger.info(f"Mouse position: x={mouse_x}, y={mouse_y}")
            
            # Create a chat window with the selected text, cursor position, and source window
            ChatWindow(selected_text, llm_service, mouse_x, mouse_y, active_window)
        else:
            logger.warning("No text selected or text capture failed")
            
            # Show an error dialog to the user
            error_window = ctk.CTkToplevel(root)
            error_window.title("SnipAI - No Text Selected")
            error_window.geometry("350x180")
            error_window.attributes("-topmost", True)
            
            # Center the window
            screen_width = error_window.winfo_screenwidth()
            screen_height = error_window.winfo_screenheight()
            x = (screen_width - 350) // 2
            y = (screen_height - 180) // 2
            error_window.geometry(f"+{x}+{y}")
            
            # Configure color scheme
            bg_color = "#2E2E2E"
            text_color = "#FFFFFF"
            button_color = "#4A6BDF"
            button_hover = "#3A5BCF"
            
            # Set appearance
            error_window.configure(fg_color=bg_color)
            
            # Add error message frame
            error_frame = ctk.CTkFrame(error_window, fg_color=bg_color)
            error_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Add icon or warning symbol
            warning_label = ctk.CTkLabel(
                error_frame,
                text="⚠️",
                font=("Helvetica", 24),
                text_color="#FFCC00"
            )
            warning_label.pack(pady=(5, 0))
            
            # Add error message
            message_label = ctk.CTkLabel(
                error_frame, 
                text="No text was selected.\n\nPlease select some text before pressing the Alt+Shift+S hotkey.",
                font=("Helvetica", 12),
                wraplength=280,
                text_color=text_color
            )
            message_label.pack(pady=10)
            
            # Add close button
            close_button = ctk.CTkButton(
                error_frame, 
                text="OK", 
                command=error_window.destroy,
                fg_color=button_color,
                hover_color=button_hover,
                width=100
            )
            close_button.pack(pady=10)
            
    except Exception as e:
        logger.error(f"Error in trigger_chat_popup: {str(e)}")

def main():
    """Main entry point for the SnipAI application."""
    global llm_service, root
    
    try:
        logger.info("Starting SnipAI application")

        # Initialize GUI root early for potential error popups
        try:
            ctk.set_appearance_mode("System")  # Or "dark"/"light"
            ctk.set_default_color_theme("blue")
            root = ctk.CTk()
            logger.info("GUI root initialized.")
        except Exception as gui_error:
            logger.critical(f"Failed to initialize GUI: {gui_error}", exc_info=True)
            # Use standard tkinter messagebox if CTk fails
            messagebox.showerror("SnipAI Critical Error", f"Failed to initialize GUI:\n{gui_error}\n\nSnipAI cannot start.")
            return  # Exit if GUI fails
        
        # Load Configuration
        try:
            groq_api_key = config.get_groq_api_key() 
            hotkey = config.get_hotkey() 
            model_name = config.get_llm_model_name() 
            logger.info("Configuration loaded successfully.")

        except ValueError as ve:
            # Log the specific configuration error
            logger.critical(f"Configuration Error: {ve}")
            logger.critical("SnipAI cannot start due to invalid or missing configuration.")
            
            # --- Create and show custom error dialog ---
            try:
                # Create a window for the error popup
                error_window = ctk.CTkToplevel(root)
                error_window.title("SnipAI - Configuration Error")
                error_window.geometry("400x250")
                error_window.attributes("-topmost", True)
                
                # Center the window on screen
                screen_width = error_window.winfo_screenwidth()
                screen_height = error_window.winfo_screenheight()
                x = (screen_width - 400) // 2
                y = (screen_height - 250) // 2
                error_window.geometry(f"+{x}+{y}")
                
                # Configure color scheme
                bg_color = "#2E2E2E"
                text_color = "#FFFFFF"
                error_color = "#FF5252"  # Red for error
                button_color = "#4A6BDF"
                button_hover = "#3A5BCF"
                
                # Set appearance
                error_window.configure(fg_color=bg_color)
                
                # Add error message frame
                error_frame = ctk.CTkFrame(error_window, fg_color=bg_color)
                error_frame.pack(fill="both", expand=True, padx=20, pady=20)
                
                # Add error icon/symbol
                error_label = ctk.CTkLabel(
                    error_frame,
                    text="❌",  # Error symbol
                    font=("Helvetica", 32),
                    text_color=error_color
                )
                error_label.pack(pady=(5, 10))
                
                # Add error title
                title_label = ctk.CTkLabel(
                    error_frame,
                    text="Configuration Error",
                    font=("Helvetica", 16, "bold"),
                    text_color=error_color
                )
                title_label.pack(pady=(0, 10))
                
                # Add error message
                error_message = f"Failed to load configuration: {ve}\n\nPlease ensure 'config.json' exists and contains valid entries for 'GROQ_API_KEY' and 'SNIPAI_HOTKEY'."
                message_label = ctk.CTkLabel(
                    error_frame, 
                    text=error_message,
                    font=("Helvetica", 12),
                    wraplength=360,
                    justify="left",
                    text_color=text_color
                )
                message_label.pack(pady=10)
                
                # Add close button
                close_button = ctk.CTkButton(
                    error_frame, 
                    text="Exit",
                    command=error_window.destroy,
                    fg_color=button_color,
                    hover_color=button_hover,
                    width=100
                )
                close_button.pack(pady=10)
                
                # Make sure the app exits after closing this dialog
                error_window.protocol("WM_DELETE_WINDOW", lambda: sys.exit(1))
                
                # Wait for user to close the dialog
                error_window.wait_window()
            except Exception as dialog_err:
                logger.error(f"Error creating config error dialog: {dialog_err}")
            
            return  # Exit the application after showing the error
        
        # Initialize Services (only if config loaded)
        logger.info("Initializing LLM service...")
        llm_service = GroqLLMService(groq_api_key, model_name)
        logger.info("LLM service initialized.")
        
        # Register Hotkey (only if config loaded)
        logger.info(f"Registering hotkey '{hotkey}'...")
        hotkey_thread = threading.Thread(
            target=lambda: hotkey_manager.setup_hotkey(hotkey, trigger_chat_popup),
            daemon=True
        )
        hotkey_thread.start()
        logger.info(f"Hotkey '{hotkey}' registered. SnipAI is running.")
        print(f"SnipAI is running. Press {hotkey} after selecting text.")
        print("Check the 'logs' folder for detailed logs.")
        
        # --- Show Success Popup --- 
        try:
            # Create a window for the success popup
            success_window = ctk.CTkToplevel(root)
            success_window.title("SnipAI - Ready")
            success_window.geometry("400x220")
            success_window.attributes("-topmost", True)
            
            # Center the window on screen
            screen_width = success_window.winfo_screenwidth()
            screen_height = success_window.winfo_screenheight()
            x = (screen_width - 400) // 2
            y = (screen_height - 220) // 2
            success_window.geometry(f"+{x}+{y}")
            
            # Configure color scheme
            bg_color = "#2E2E2E"
            text_color = "#FFFFFF"
            success_color = "#4CAF50"  # Green for success
            button_color = "#4A6BDF"
            button_hover = "#3A5BCF"
            
            # Set appearance
            success_window.configure(fg_color=bg_color)
            
            # Add success message frame
            success_frame = ctk.CTkFrame(success_window, fg_color=bg_color)
            success_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Add success icon/symbol
            success_label = ctk.CTkLabel(
                success_frame,
                text="✓",  # Success symbol
                font=("Helvetica", 32),
                text_color=success_color
            )
            success_label.pack(pady=(5, 10))
            
            # Add success title
            title_label = ctk.CTkLabel(
                success_frame,
                text="SnipAI Ready",
                font=("Helvetica", 16, "bold"),
                text_color=success_color
            )
            title_label.pack(pady=(0, 10))
            
            # Add success message
            success_message = f"SnipAI has started successfully!\n\nPress '{hotkey}' after selecting text to activate."
            message_label = ctk.CTkLabel(
                success_frame, 
                text=success_message,
                font=("Helvetica", 12),
                wraplength=360,
                text_color=text_color
            )
            message_label.pack(pady=10)
            
            # Add OK button
            ok_button = ctk.CTkButton(
                success_frame, 
                text="OK",
                command=success_window.destroy,
                fg_color=button_color,
                hover_color=button_hover,
                width=100
            )
            ok_button.pack(pady=10)
        except Exception as popup_err:
            logger.error(f"Failed to show success popup: {popup_err}")
            # Continue running even if success popup fails
        
        # Hide the root window after showing the success popup
        root.withdraw()
        
        # Start the main GUI loop (only if everything initialized)
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)
        # Show a generic critical error popup
        error_title = "SnipAI Critical Error"
        error_message = f"An unexpected critical error occurred:\n\n{e}\n\nPlease check the logs for details.\nSnipAI will now exit."
        try:
            from CTkMessagebox import CTkMessagebox
            CTkMessagebox(title=error_title, message=error_message, icon="cancel")
        except ImportError:
            messagebox.showerror(error_title, error_message)
        except Exception as popup_err:  # Catch errors showing the popup itself
            logger.error(f"Failed to show critical error popup: {popup_err}")
            print(f"CRITICAL ERROR: {e}. Check logs.")  # Fallback print
    
    finally:
        # Clean up
        if root and root.winfo_exists():  # Check if root exists before destroying
            try:
                root.destroy()
            except Exception as destroy_err:
                logger.error(f"Error destroying root window: {destroy_err}")
        logger.info("SnipAI application stopped")

if __name__ == "__main__":
    main()

