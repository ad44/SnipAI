"""
Chat window module for the SnipAI application.
Defines the popup chat GUI using customtkinter.
"""
import threading
import logging
import customtkinter as ctk
import json
import re
import keyboard
import time
import pyperclip
import pyautogui  # Import pyautogui for screen dimensions

# Configure logging
logger = logging.getLogger(__name__)

class ChatWindow(ctk.CTkToplevel):
    """
    Popup chat window for the SnipAI application.
    """
    
    def __init__(self, initial_text, llm_service, mouse_x=None, mouse_y=None, source_window=None):
        """
        Initialize the chat window.
        
        Args:
            initial_text (str): The text selected by the user.
            llm_service (GroqLLMService): Instance of the LLM service.
            mouse_x (int, optional): X-coordinate of the mouse cursor.
            mouse_y (int, optional): Y-coordinate of the mouse cursor.
            source_window: The window where text was selected.
        """
        super().__init__()
        
        self.initial_text = initial_text
        self.llm_service = llm_service
        # Stack to store original and enhanced texts
        self.text_stack = [self.initial_text]  # Initialize stack with original text
        self.enhanced_content = self.initial_text  # Start with initial text
        self.source_window = source_window  # Store the source window reference
        self._paste_button_flash_timer = None  # Add timer tracker
        
        # Configure window
        self.title("SnipAI")
        self.geometry("300x300")  # Window size
        self.attributes("-topmost", True)
        
        # Calculate and set optimal window position
        self._calculate_window_position(mouse_x, mouse_y)
        
        # Set up color scheme
        self.bg_color = "#2E2E2E"
        self.text_color = "#FFFFFF"
        self.input_bg = "#3E3E3E"
        self.button_color = "#4A6BDF"
        self.button_hover = "#3A5BCF"
        self.context_bg = "#252525"
        self.paste_button_color = "#50A050"  # Green color for paste button
        self.paste_button_hover = "#408040"
        self.undo_button_color = "#4A6BDF"  # Match main button color for consistency
        self.undo_button_hover = "#3A5BCF"  # Match main button hover color
        self.undo_button_disabled_color = "#555555"  # Slightly darker gray for better visibility
        
        # Configure appearance
        ctk.set_appearance_mode("dark")  # Force dark mode for better aesthetics
        self.configure(fg_color=self.bg_color)
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Context frame - fixed size
        self.grid_rowconfigure(1, weight=1)  # Chat display - expands
        self.grid_rowconfigure(2, weight=0)  # Input area - fixed size
        self.grid_rowconfigure(3, weight=0)  # Paste button area - fixed size (hidden initially)
        
        # Create context frame (collapsible)
        self.context_frame = ctk.CTkFrame(self, fg_color=self.context_bg, corner_radius=6)
        self.context_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.context_frame.grid_columnconfigure(0, weight=1)
        
        # Context header with toggle button
        self.context_header = ctk.CTkFrame(self.context_frame, fg_color="transparent")
        self.context_header.grid(row=0, column=0, sticky="ew", padx=2, pady=(2,0))
        self.context_header.grid_columnconfigure(0, weight=1)
        self.context_header.grid_columnconfigure(1, weight=0)
        
        self.context_label = ctk.CTkLabel(
            self.context_header, 
            text="Selected Text", 
            fg_color="transparent",
            text_color="#BBBBBB",
            anchor="w"
        )
        self.context_label.grid(row=0, column=0, sticky="w", padx=5)
        
        self.is_context_expanded = False
        self.toggle_button = ctk.CTkButton(
            self.context_header,
            text="▼",
            width=24,
            height=24,
            corner_radius=4,
            fg_color=self.context_bg,
            hover_color=self.input_bg,
            text_color="#BBBBBB",
            command=self._toggle_context
        )
        self.toggle_button.grid(row=0, column=1, padx=2, pady=2)
        
        # Context preview (one line summary)
        preview_text = self.initial_text.strip().split("\n")[0]
        if len(preview_text) > 50:
            preview_text = preview_text[:47] + "..."
        
        self.context_preview = ctk.CTkLabel(
            self.context_frame, 
            text=preview_text,
            fg_color="transparent", 
            text_color="#DDDDDD",
            anchor="w",
            wraplength=320
        )
        self.context_preview.grid(row=1, column=0, sticky="ew", padx=5, pady=(0,5))
        
        # Full context text (hidden initially)
        self.context_full = ctk.CTkTextbox(
            self.context_frame,
            height=80,
            fg_color=self.context_bg,
            border_width=0,
            wrap="word",
            text_color="#DDDDDD"
        )
        self.context_full.grid(row=2, column=0, sticky="ew", padx=5, pady=(0,5))
        self.context_full.insert("1.0", self.initial_text)
        self.context_full.configure(state="disabled")
        self.context_full.grid_remove()  # Hide initially
        
        # Create chat display
        self.chat_display = ctk.CTkTextbox(
            self, 
            wrap="word",
            fg_color=self.bg_color,
            text_color=self.text_color,
            border_width=0,
            corner_radius=0
        )
        self.chat_display.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 0))
        self.chat_display.configure(state="disabled")
        
        # Create input frame
        self.input_frame = ctk.CTkFrame(self, fg_color=self.bg_color, corner_radius=0)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=0)
        
        # Create input field
        self.user_input = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Ask about the text...",
            fg_color=self.input_bg,
            border_width=0,
            height=30,
            corner_radius=15
        )
        self.user_input.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Create send button
        self.send_button = ctk.CTkButton(
            self.input_frame, 
            text="Send", 
            width=50,
            height=30,
            command=self._send_message_event,
            fg_color=self.button_color,
            hover_color=self.button_hover,
            corner_radius=15
        )
        self.send_button.grid(row=0, column=1, sticky="e")
        
        # Create paste button frame (hidden initially)
        self.paste_frame = ctk.CTkFrame(self, fg_color=self.bg_color, corner_radius=0)
        self.paste_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.paste_frame.grid_remove()  # Hide initially
        self.paste_frame.grid_columnconfigure(0, weight=1)  # Allow content to expand

        # Add a preview label that will show a snippet of enhanced content
        self.paste_preview = ctk.CTkLabel(
            self.paste_frame,
            text="",  # Initially empty
            fg_color="transparent",
            text_color="#CCCCCC",
            anchor="w",
            wraplength=280,
            justify="left",
            height=10  # Minimal height initially
        )
        self.paste_preview.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 5))

        # Create a frame specifically for the action buttons (Paste, Undo)
        self.action_button_frame = ctk.CTkFrame(self.paste_frame, fg_color="transparent")
        self.action_button_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.action_button_frame.grid_columnconfigure(0, weight=1)  # Paste button takes available space
        self.action_button_frame.grid_columnconfigure(1, weight=0)  # Undo button fixed width

        # Create paste button
        self.paste_button = ctk.CTkButton(
            self.action_button_frame,  # Place in the button frame
            text="Paste",  # Shorter text
            command=self._paste_enhanced_content,
            fg_color=self.paste_button_color,
            hover_color=self.paste_button_hover,
            corner_radius=15,
            font=("Helvetica", 12, "bold"),
            height=36
        )
        self.paste_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))  # Grid layout, add padding to right

        # Create undo button
        self.undo_button = ctk.CTkButton(
            self.action_button_frame,  # Place in the button frame
            text="Undo",
            command=self._undo_action,
            fg_color=self.undo_button_color,
            hover_color=self.undo_button_hover,
            corner_radius=15,
            font=("Helvetica", 12, "bold"),
            height=36,
            width=80,  # Fixed width for undo button
            state="disabled"  # Initially disabled
        )
        self.undo_button.grid(row=0, column=1, sticky="e")  # Grid layout
        
        # Bind Enter key to send message
        self.user_input.bind("<Return>", self._send_message_event)
        
        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Focus the input field
        self.user_input.focus_set()
        
        # Log source window information
        if source_window:
            try:
                logger.info(f"Source window stored: {source_window.title}")
            except Exception as e:
                logger.error(f"Error accessing source window properties: {str(e)}")
        
        logger.info("Chat window initialized")
    
    def _calculate_window_position(self, mouse_x, mouse_y):
        """
        Calculate the optimal position for the window based on cursor position and screen size.
        
        Args:
            mouse_x (int, optional): X-coordinate of the mouse cursor.
            mouse_y (int, optional): Y-coordinate of the mouse cursor.
        """
        # If mouse position wasn't provided, center on screen
        if mouse_x is None or mouse_y is None:
            self.update_idletasks()  # Make sure window size is updated
            window_width = self.winfo_width() or 300  # Default if winfo_width returns 0
            window_height = self.winfo_height() or 300  # Default if winfo_height returns 0
            
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Center the window
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            logger.info(f"Centering window on screen at position: x={x}, y={y}")
            self.geometry(f"+{x}+{y}")
            return
            
        # Get screen dimensions
        screen_width = pyautogui.size()[0]
        screen_height = pyautogui.size()[1]
        
        # Get window dimensions
        # Note: During __init__, the window hasn't been fully realized yet,
        # so we use the default size we set
        window_width = 300
        window_height = 300
        
        # Calculate position to the right of the cursor
        x = mouse_x + 20  # Add some padding
        
        # If placing to the right would make the window go off screen,
        # place it to the left of the cursor instead
        if x + window_width > screen_width:
            x = mouse_x - window_width - 20
        
        # If placing to the left would make the window go off screen (e.g., cursor at left edge),
        # center the window horizontally
        if x < 0:
            x = (screen_width - window_width) // 2
        
        # Calculate vertical position (try to center vertically with the cursor)
        y = mouse_y - (window_height // 2)
        
        # Make sure the window is not positioned off the top of the screen
        if y < 0:
            y = 10  # Add some padding from the top
        
        # Make sure the window is not positioned off the bottom of the screen
        if y + window_height > screen_height:
            y = screen_height - window_height - 40  # Add some padding from the bottom
        
        logger.info(f"Positioning window at: x={x}, y={y}")
        self.geometry(f"+{x}+{y}")
    
    def _toggle_context(self):
        """Toggle the visibility of the full context"""
        self.is_context_expanded = not self.is_context_expanded
        
        if self.is_context_expanded:
            self.context_preview.grid_remove()  # Hide preview
            self.context_full.grid()  # Show full context
            self.toggle_button.configure(text="▲")  # Change toggle icon
        else:
            self.context_full.grid_remove()  # Hide full context
            self.context_preview.grid()  # Show preview
            self.toggle_button.configure(text="▼")  # Change toggle icon
    
    def _send_message_event(self, event=None):
        """
        Handle send message event (button click or Enter key).
        
        Args:
            event: The event that triggered this function (ignored).
        """
        # Get user input
        user_text = self.user_input.get().strip()
        if not user_text:
            return
        
        # Clear input field
        self.user_input.delete(0, 'end')
        
        # Display user message
        self._append_to_chat(user_text, role="user")
        self._append_to_chat("Thinking...", role="status")
        
        # Disable input while waiting for response
        self._set_input_state("disabled")
        
        # Hide paste button if visible from previous interaction
        self.paste_frame.grid_remove()
        self.enhanced_content = None
        
        # Check if this is the first message
        if self.chat_display.get("1.0", "end").count("AI:") == 0:
            # This is the first user message, include context
            threading.Thread(
                target=self._get_initial_response,
                args=(user_text,),
                daemon=True
            ).start()
        else:
            # Regular follow-up message
            threading.Thread(
                target=self._get_ai_response,
                args=(user_text,),
                daemon=True
            ).start()
    
    def _get_initial_response(self, user_text):
        """Get the initial response from the LLM in a separate thread with context."""
        try:
            # Create the initial conversation with both the selected text and the user's first question
            initial_prompt = f"""Selected text:
```
{self.initial_text}
```
User question: {user_text}

If the user is requesting to enhance, modify, or transform the text in any way,
include a JSON block with the enhanced content in the following format:
```json
{{"enhanced_content": "The enhanced text goes here"}}
```
Only include this JSON block if the user explicitly asks for text enhancement, rewriting, etc."""
            
            # Initialize the conversation with both context and question
            self.llm_service.memory.clear()  # Make sure memory is clear
            ai_response = self.llm_service.invoke_chain(initial_prompt)
            
            # Check for enhanced content in the response
            cleaned_text, enhanced_content = self._extract_enhanced_content(ai_response)
            
            # Update the GUI with the response
            self.after(0, self._update_gui_from_thread, cleaned_text, "assistant", enhanced_content)
        except Exception as e:
            error_message = f"Error getting response: {str(e)}"
            logger.error(error_message)
            self.after(0, self._update_gui_from_thread, error_message, "error")
    
    def _get_ai_response(self, user_text):
        """Get AI response for follow-up messages."""
        try:
            # Add instruction to include enhanced content if requested
            full_prompt = f"""{user_text}

If the user is requesting to enhance, modify, or transform text in any way,
include a JSON block with the enhanced content in the following format:
```json
{{"enhanced_content": "The enhanced text goes here"}}
```
Only include this JSON block if the user explicitly asks for text enhancement, rewriting, etc."""
            
            ai_response = self.llm_service.invoke_chain(full_prompt)
            
            # Check for enhanced content in the response
            cleaned_text, enhanced_content = self._extract_enhanced_content(ai_response)
            
            self.after(0, self._update_gui_from_thread, cleaned_text, "assistant", enhanced_content)
        except Exception as e:
            error_message = f"Error getting response: {str(e)}"
            logger.error(error_message)
            self.after(0, self._update_gui_from_thread, error_message, "error")
    
    def _extract_enhanced_content(self, text):
        """
        Extract enhanced content from JSON block in the response and clean up display text.
        Returns a tuple of (cleaned_text, enhanced_content).
        """
        try:
            # Look for JSON pattern with enhanced_content
            json_pattern = r'```json\s*({.*?"enhanced_content"\s*:.*?})\s*```'
            matches = re.search(json_pattern, text, re.DOTALL)
            
            if matches:
                json_str = matches.group(1)
                data = json.loads(json_str)
                if "enhanced_content" in data:
                    # Get the enhanced content
                    enhanced_content = data["enhanced_content"]
                    logger.info(f"Enhanced content found in response: {len(enhanced_content)} characters")
                    
                    # Clean up the display text by removing the JSON block
                    cleaned_text = re.sub(json_pattern, '', text, flags=re.DOTALL).strip()
                    
                    # Fix any double newlines created by removing the JSON block
                    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
                    
                    return cleaned_text, enhanced_content
        
        except Exception as e:
            logger.warning(f"Error extracting enhanced content: {e}")
        
        # If no enhanced content or error, return original text and None
        return text, None
    
    def _update_gui_from_thread(self, message, role, enhanced_content=None):
        """Update the GUI from a thread via after() method."""
        # Remove the "Thinking..." message
        self._remove_last_message()
        
        # Check if the message is a categorized error
        if role == "assistant" and message.startswith(("API_KEY_ERROR:", "CONNECTION_ERROR:", "NO_RESPONSE_ERROR:")):
            # Extract error type and message
            error_parts = message.split(":", 1)
            error_type = error_parts[0].replace("_", " ")
            error_message = error_parts[1].strip() if len(error_parts) > 1 else "Unknown error"
            
            # Display as error with appropriate icon and styling
            self._append_to_chat(f"⚠️ {error_type}", "error_title")
            self._append_to_chat(error_message, "error")
            
            # Re-enable input
            self._set_input_state("normal")
            return
        
        # Display the new message normally
        self._append_to_chat(message, role)
        
        # Save enhanced content if present
        if enhanced_content:
            # Add new enhanced content to stack if it's different from the current content
            if enhanced_content != self.enhanced_content:
                self.text_stack.append(enhanced_content)
                self.undo_button.configure(state="normal")
                logger.info("Undo button enabled (new enhanced content added)")
            
            self.enhanced_content = enhanced_content
            
            # Show paste button and frame
            self.paste_frame.grid()
            
            # Update the preview label with the new content
            self._update_paste_preview()
            
        # Re-enable input if not an error
        if role != "error":
            self._set_input_state("normal")
    
    def _undo_action(self):
        """Reverts the enhanced_content to the previous version in stack and selects it in the source window."""
        if len(self.text_stack) > 1:
            # Pop the current content from stack
            self.text_stack.pop()  
            
            # Set the enhanced content to previous version
            self.enhanced_content = self.text_stack[-1]
            logger.info(f"Undo action: Reverted to previous content in stack")

            # Update the preview label
            self._update_paste_preview()

            # Disable undo button if we are back at the original text
            if len(self.text_stack) == 1:
                self.undo_button.configure(state="disabled", fg_color=self.undo_button_disabled_color)
                logger.info("Undo button disabled (at original text)")
            
            # Apply the undone text to the source window with selection
            self._apply_text_to_source_window(self.enhanced_content, "Undone")
    
    def _apply_text_to_source_window(self, text_content, action_name="Pasted"):
        """Apply text to source window and select it, used by both paste and undo operations."""
        if not text_content:
            return False
        
        try:
            # Save original clipboard content
            original_content = pyperclip.paste()
            
            # Set new content to clipboard
            pyperclip.copy(text_content)
            
            # Calculate the number of characters for selection
            content_length = len(text_content)
            
            # Check if we have a valid source window reference
            if self.source_window:
                try:
                    # Get current active window for later restoration
                    import pygetwindow as gw
                    current_window = gw.getActiveWindow()
                    
                    # Try to activate the source window
                    self.source_window.activate()
                    
                    # Give time for window to activate
                    time.sleep(0.5)
                    
                    # Paste the content
                    keyboard.press_and_release('ctrl+v')
                    
                    # Give time for paste operation to complete
                    time.sleep(0.3)
                    
                    # Select the pasted text by using Shift+Left arrows
                    keyboard.press('shift')
                    for _ in range(min(content_length, 1000)):  # Limit to 1000 keystrokes for very long content
                        keyboard.press_and_release('left')
                        time.sleep(0.001)  # Small delay between keypresses
                    keyboard.release('shift')
                    
                    # Return focus to our window after a brief delay
                    time.sleep(0.5)
                    if current_window:
                        current_window.activate()
                    
                    # Show success via button only (no chat message)
                    self._flash_paste_button_success(f"Content {action_name} Successfully!")
                    
                    # Set a timer to restore clipboard after 10 seconds
                    def restore_clipboard():
                        try:
                            current = pyperclip.paste()
                            if current == text_content:
                                pyperclip.copy(original_content)
                                logger.info("Original clipboard content restored after timeout")
                        except Exception as e:
                            logger.error(f"Error restoring clipboard: {e}")
                    
                    threading.Timer(10.0, restore_clipboard).start()
                    return True
                    
                except Exception as e:
                    logger.error(f"Error during {action_name.lower()} operation: {e}")
                    return False
            else:
                # No source window reference
                return False
                
        except Exception as e:
            logger.error(f"Error during {action_name.lower()} operation: {e}")
            return False
    
    def _update_paste_preview(self):
        """Updates the paste preview label with the current enhanced_content."""
        preview_text = self.enhanced_content.strip().replace('\n', ' ')[:60]  # Show first 60 chars, no newlines
        if len(self.enhanced_content) > 60:
            preview_text += "..."
        self.paste_preview.configure(text=f"Paste: {preview_text}")

    def _paste_enhanced_content(self):
        """Paste the enhanced content by switching to source window and select after pasting."""
        if not self.enhanced_content:
            logger.warning("No enhanced content to paste")
            # Don't show message in chat, just update button
            self._flash_paste_button_ready("No content to paste!")
            return
            
        # Apply the content to the source window
        paste_successful = self._apply_text_to_source_window(self.enhanced_content)
        
        if paste_successful:
            # Add content to stack if successful paste and if it's not already at the top of the stack
            if self.text_stack[-1] != self.enhanced_content:
                self.text_stack.append(self.enhanced_content)
                
            # Always enable the undo button if we have more than one item in stack
            if len(self.text_stack) > 1:
                self.undo_button.configure(
                    state="normal",
                    fg_color=self.undo_button_color,
                    hover_color=self.undo_button_hover
                )
                logger.info("Undo button enabled (content pasted successfully)")
            
            # Update the preview in case we added the content to the stack
            self._update_paste_preview()
    
    def _flash_paste_button_success(self, message="Content Pasted Successfully!"):
        """
        Change the paste button appearance to indicate successful paste.
        Ensures only one flash timer runs at a time.
        """
        # Cancel any existing timer
        if self._paste_button_flash_timer:
            self.after_cancel(self._paste_button_flash_timer)
            self._paste_button_flash_timer = None
            
        # Save original colors, text and state
        original_color = self.paste_button.cget("fg_color")
        original_hover = self.paste_button.cget("hover_color")
        original_text = self.paste_button.cget("text")
        
        # Change to success color and disable button
        success_color = "#50A050"  # Green color
        success_hover = "#408040"
        self.paste_button.configure(
            fg_color=success_color,
            hover_color=success_hover,
            text=message,
            state="disabled"  # Disable button while showing message
        )
        
        # Schedule revert after exactly 1.2 seconds
        def revert_button():
            if hasattr(self, 'paste_button') and self.paste_button.winfo_exists():
                self.paste_button.configure(
                    fg_color=original_color,
                    hover_color=original_hover,
                    text=original_text,
                    state="normal"  # Re-enable button
                )
            self._paste_button_flash_timer = None # Clear timer ID
            
        self._paste_button_flash_timer = self.after(1200, revert_button)  # 1200ms = 1.2 seconds
    
    def _flash_paste_button_ready(self, message_text="Content Ready! Click where you want to paste"):
        """
        Change the paste button appearance to indicate content is ready to paste.
        Ensures only one flash timer runs at a time.
        """
        # Cancel any existing timer
        if self._paste_button_flash_timer:
            self.after_cancel(self._paste_button_flash_timer)
            self._paste_button_flash_timer = None
            
        # Save original colors and state
        original_color = self.paste_button.cget("fg_color")
        original_hover = self.paste_button.cget("hover_color")
        original_text = self.paste_button.cget("text")
        
        # Change to ready color and disable button
        ready_color = "#4A90E2"  # Blue color
        ready_hover = "#3A80D2"
        self.paste_button.configure(
            fg_color=ready_color,
            hover_color=ready_hover,
            text=message_text,
            state="disabled"  # Disable button while showing message
        )
        
        # Schedule revert after exactly 1.2 seconds
        def revert_button():
            if hasattr(self, 'paste_button') and self.paste_button.winfo_exists():
                self.paste_button.configure(
                    fg_color=original_color,
                    hover_color=original_hover,
                    text=original_text,
                    state="normal"  # Re-enable button
                )
            self._paste_button_flash_timer = None # Clear timer ID
            
        self._paste_button_flash_timer = self.after(1200, revert_button)  # 1200ms = 1.2 seconds
    
    def _flash_paste_button_info(self, message, duration=None):
        """
        Flash the paste button with an informational message for exactly 1.2 seconds.
        Ensures only one flash timer runs at a time.
        """
        # Cancel any existing timer
        if self._paste_button_flash_timer:
            self.after_cancel(self._paste_button_flash_timer)
            self._paste_button_flash_timer = None
            
        # Save original colors, text and state
        original_color = self.paste_button.cget("fg_color")
        original_hover = self.paste_button.cget("hover_color")
        original_text = self.paste_button.cget("text")
        
        # Change to info color and disable button
        info_color = "#E0E060"  # Yellow color
        info_hover = "#D0D050"
        self.paste_button.configure(
            fg_color=info_color,
            hover_color=info_hover,
            text=message,
            state="disabled"  # Disable button while showing message
        )
        
        # Schedule revert after exactly 1.2 seconds, ignoring the duration parameter
        def revert_button():
            if hasattr(self, 'paste_button') and self.paste_button.winfo_exists():
                self.paste_button.configure(
                    fg_color=original_color,
                    hover_color=original_hover,
                    text=original_text,
                    state="normal"  # Re-enable button
                )
            self._paste_button_flash_timer = None # Clear timer ID
            
        self._paste_button_flash_timer = self.after(1200, revert_button)  # Always 1200ms (1.2 seconds)
    
    def _remove_message_by_id_if_exists(self, message_id):
        """Remove a message by ID if it exists"""
        if message_id:
            self._remove_message_by_id(message_id)
    
    def _append_to_chat_with_id(self, message, role):
        """
        Append a message to the chat display with styling and return a unique ID for this message.
        This allows for selective removal later.
        
        Args:
            message (str): The message to append.
            role (str): The role of the message sender.
            
        Returns:
            str: A unique ID for this message to allow removal later.
        """
        # Create a unique ID for this message
        message_id = f"msg_{time.time()}_{id(message)}"
        self._last_message_id = message_id
        
        # Enable the text widget for editing
        self.chat_display.configure(state="normal")
        
        # Add a prefix based on the role
        if role == "user":
            prefix = "You: "
            color = "#5E9DFF"  # Light blue for user
        elif role == "assistant":
            prefix = "AI: "
            color = "#50D050"  # Green for AI
        elif role == "error":
            prefix = "Error: "
            color = "#FF5050"  # Red for errors
        elif role == "status":
            prefix = ""  # No prefix for status
            color = "#AAAAAA"  # Gray for status
        elif role == "system":
            prefix = "System: "
            color = "#E0E060"  # Yellow for system messages
        else:
            prefix = f"{role.capitalize()}: "
            color = self.text_color
        
        # Insert message with prefix
        if self.chat_display.index('end-1c') != '1.0':  # Not the first line
            self.chat_display.insert('end', '\n\n')
            
        # Store the start position of this message
        message_start = self.chat_display.index('end-1c')
        
        # Add the message
        self.chat_display.insert('end', f"{prefix}{message}")
        message_end = self.chat_display.index('end-1c')
        
        # Apply color to the text
        self.chat_display.tag_add(role, message_start, message_end)
        self.chat_display.tag_config(role, foreground=color)
        
        # Also tag with the unique ID for later removal
        self.chat_display.tag_add(message_id, message_start, message_end)
        
        # Disable the text widget again
        self.chat_display.configure(state="disabled")
        
        # Scroll to the bottom
        self.chat_display.yview_moveto(1.0)
        
        return message_id
    
    def _remove_message_by_id(self, message_id):
        """
        Remove a specific message from the chat display using its ID.
        
        Args:
            message_id (str): The unique ID of the message to remove.
        """
        if not message_id:
            return
            
        try:
            # Enable the text widget for editing
            self.chat_display.configure(state="normal")
            
            # Find the range of the message with this ID
            ranges = self.chat_display.tag_ranges(message_id)
            
            if ranges and len(ranges) >= 2:
                # Get the start and end positions
                start = ranges[0]
                end = ranges[1]
                
                # Check if we need to remove preceding newlines
                # This makes the chat flow more naturally after removal
                prev_char_pos = self.chat_display.index(f"{start} - 1 chars")
                next_char_pos = self.chat_display.index(f"{end} + 1 chars")
                
                # If preceded by newlines, remove them too
                if self.chat_display.get(prev_char_pos, start) == "\n":
                    start = prev_char_pos
                
                # If followed by newlines, remove one of them
                if self.chat_display.get(end, next_char_pos) == "\n":
                    end = next_char_pos
                
                # Delete the message
                self.chat_display.delete(start, end)
            
            # Disable the text widget again
            self.chat_display.configure(state="disabled")
            
        except Exception as e:
            logger.error(f"Error removing message by ID: {e}")
    
    def _remove_last_message(self):
        """Remove the last message from the chat display (usually a status message)."""
        self.chat_display.configure(state="normal")
        
        # Get the last line index
        last_line_start = self.chat_display.index("end-1l linestart")
        
        # Delete the last line
        self.chat_display.delete(last_line_start, "end")
        
        self.chat_display.configure(state="disabled")
    
    def _set_input_state(self, state):
        """
        Set the state of input widgets.
        
        Args:
            state (str): The state to set ('normal' or 'disabled').
        """
        self.user_input.configure(state=state)
        self.send_button.configure(state=state)
    
    def _append_to_chat(self, message, role):
        """
        Append a message to the chat display with styling.
        
        Args:
            message (str): The message to append.
            role (str): The role of the message sender.
        """
        # Enable the text widget for editing
        self.chat_display.configure(state="normal")
        
        # Add a prefix based on the role
        if role == "user":
            prefix = "You: "
            color = "#5E9DFF"  # Light blue for user
        elif role == "assistant":
            prefix = "AI: "
            color = "#50D050"  # Green for AI
        elif role == "error":
            prefix = "Error: "
            color = "#FF5050"  # Red for errors
        elif role == "status":
            prefix = ""  # No prefix for status
            color = "#AAAAAA"  # Gray for status
        elif role == "system":
            prefix = "System: "
            color = "#E0E060"  # Yellow for system messages
        else:
            prefix = f"{role.capitalize()}: "
            color = self.text_color
        
        # Insert message with prefix
        if self.chat_display.index('end-1c') != '1.0':  # Not the first line
            self.chat_display.insert('end', '\n\n')
        
        # Add the message
        message_start = self.chat_display.index('end-1c')
        self.chat_display.insert('end', f"{prefix}{message}")
        message_end = self.chat_display.index('end-1c')
        
        # Apply color to the text
        self.chat_display.tag_add(role, message_start, message_end)
        self.chat_display.tag_config(role, foreground=color)
        
        # Disable the text widget again
        self.chat_display.configure(state="disabled")
        
        # Scroll to the bottom
        self.chat_display.yview_moveto(1.0)
    
    def on_close(self):
        """Handle window closing."""
        logger.info("Chat window closed")
        self.destroy()

# Test function for when this module is run directly
def test_chat_window():
    """
    Simple test function to run when this module is executed directly.
    Creates a mock LLM service and launches the chat window with sample text.
    """
    import time
    
    # Configure logging for the test
    logging.basicConfig(level=logging.INFO)
    
    # Create a mock LLM service for testing
    class MockLLMService:
        def __init__(self):
            self.memory = type('obj', (object,), {'clear': lambda: None})
            
        def invoke_chain(self, user_input):
            print(f"Mock LLM received: {user_input[:50]}...")
            time.sleep(1)  # Simulate API delay
            
            # If the input contains "enhance" or "rewrite", include enhanced content
            if "enhance" in user_input.lower() or "rewrite" in user_input.lower():
                return f"""I've enhanced the text as requested.

```json
{"enhanced_content": "This is the enhanced version of the text. It's more polished and professional."}
```

Let me know if you need any further adjustments."""
            else:
                return f"Mock response to your question about the selected text."
    
    # Create root window (required for CTkToplevel)
    root = ctk.CTk()
    root.withdraw()
    
    # Sample text that would be selected by the user
    sample_text = """This is a sample text that would be selected by the user.
It's meant to test how the chat window handles and displays selected text.
It contains multiple lines to test the collapsible context feature."""
    
    # Create chat window with mock service
    print("Creating test chat window...")
    chat_window = ChatWindow(sample_text, MockLLMService(), mouse_x=500, mouse_y=300)
    
    # Start the main loop
    print("Test chat window created. Running main loop...")
    root.mainloop()

# Run test if this file is executed directly
if __name__ == "__main__":
    test_chat_window()