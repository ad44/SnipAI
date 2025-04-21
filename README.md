# SnipAI 🚀

**Instantly chat with and enhance selected text anywhere on Windows using the power of GenAI.**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Replace with your actual license -->

---

## 🤔 What is SnipAI?

SnipAI is a lightweight Windows utility that bridges the gap between your selected text and powerful Large Language Models (LLMs) like Llama 3 via Groq. Simply select text in *any* application, press a configurable hotkey, and instantly start a chat about that text. Ask questions, summarize, translate, rewrite, or perform any task the LLM supports, and then seamlessly paste the enhanced content back into your original application.

## ✨ Features

*   **Universal Text Capture:** Works with text selected in almost any Windows application.
*   **Instant Chat Interface:** A clean, modern chat window pops up right where you need it.
*   **LLM Integration:** Powered by Groq for fast inference with models like Llama 3.3 70b.
*   **Seamless Pasting:** Replace the original selected text with the AI-enhanced version with a single click.
*   **Undo Functionality:** Easily revert the pasted text back to the previous version.
*   **Configurable Hotkey:** Choose your preferred keyboard shortcut.
*   **External Configuration:** API key and hotkey managed via a simple `config.json` file.
*   **Standalone Executable:** No need to install Python or dependencies (packaged with PyInstaller).
*   **Background Operation:** Runs quietly in the background until you summon it.

## ⚙️ How it Works

1.  **Run:** Start `SnipAI.exe`. It runs in the background.
2.  **Select:** Highlight text in any application (browser, editor, document, etc.).
3.  **Trigger:** Press your configured hotkey (default: `Alt+Shift+D`).
4.  **Capture:** SnipAI copies the selected text.
5.  **Chat:** A chat window appears near your cursor, pre-loaded with the context.
6.  **Interact:** Ask questions or give instructions to the LLM (e.g., "Summarize this", "Translate to Hindi", "Correct grammar").
7.  **Enhance:** If the AI provides modified text, a "Paste" button appears.
8.  **Paste:** Click "Paste" to replace the original selected text in the source application with the AI's version.
9.  **Undo:** Click "Undo" to revert the changes made by the last paste operation.

## 💾 Installation & Setup

1.  **Download:** Grab the latest `SnipAI.exe` from the [Releases](https://github.com/your_username/SnipAI/releases) page. <!-- Update this link -->
2.  **Configure:**
    *   Place the downloaded `SnipAI.exe` in a folder of your choice.
    *   In the *same folder* as `SnipAI.exe`, create a file named `config.json`.
    *   Paste the following content into `config.json`:
        ```json
        {
          "GROQ_API_KEY": "YOUR_GROQ_API_KEY_HERE",
          "SNIPAI_HOTKEY": "alt+shift+d"
        }
        ```
    *   Replace `"YOUR_GROQ_API_KEY_HERE"` with your actual API key obtained from [GroqCloud](https://console.groq.com/keys).
    *   (Optional) Change `"alt+shift+d"` to your preferred hotkey combination (e.g., `"ctrl+alt+s"`). Use lowercase letters for keys and `+` to combine them. Supported modifiers: `ctrl`, `alt`, `shift`, `win`.
3.  **Run:** Double-click `SnipAI.exe`. You should see a console message indicating it's running and listening for the hotkey.
4.  **(Optional) Run on Startup:**
    *   Press `Win + R`, type `shell:startup`, and press Enter.
    *   Create a shortcut to `SnipAI.exe` in the folder that opens.

## 🚀 Usage

1.  Ensure `SnipAI.exe` is running.
2.  Select text in any application.
3.  Press the hotkey defined in your `config.json`.
4.  The chat window will appear. Type your query and press Enter or click "Send".
5.  If the AI provides enhanced text, click the "Paste" button. SnipAI will attempt to switch back to your original application, paste the content, and re-select it.
6.  If you need to revert the paste, click the "Undo" button in the chat window.

## 🔧 Configuration (`config.json`)

The application requires a `config.json` file in the same directory as the executable.

*   `GROQ_API_KEY` (Required): Your API key from GroqCloud. The application will not start without a valid key.
*   `SNIPAI_HOTKEY` (Required): The global hotkey combination to trigger SnipAI.

## 💻 Development

Interested in contributing or modifying SnipAI?

1.  **Prerequisites:** Python 3.9 or higher.
2.  **Clone:** `git clone https://github.com/your_username/SnipAI.git` <!-- Update this link -->
3.  **Navigate:** `cd SnipAI`
4.  **Environment:** Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    # source venv/bin/activate
    ```
5.  **Install:** `pip install -r req.txt`
6.  **Configure:** Create `config.json` in the project root directory (same structure as described in Installation).
7.  **Run:** `python main.py`
8.  **Build:** To create the standalone executable:
    ```bash
    pyinstaller --onefile --windowed --name SnipAI main.py
    ```
    The `.exe` will be in the `dist` folder. Remember to copy `config.json` next to it if distributing.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs, feature requests, or suggestions.

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. <!-- Create a LICENSE file if you haven't -->

## 🙏 Acknowledgements

*   [Groq](https://groq.com/) for providing the blazing-fast LLM inference API.
*   [LangChain](https://www.langchain.com/) for simplifying LLM interactions.
*   [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern GUI elements.
*   [Keyboard](https://github.com/boppreh/keyboard) for global hotkey management.
*   [Pyperclip](https://github.com/asweigart/pyperclip) for clipboard operations.
*   [PyInstaller](https://pyinstaller.org/) for packaging the application.
