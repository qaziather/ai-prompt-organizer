# Prompt Vault

A fully offline desktop workspace for saving and organizing reusable prompts. The app keeps every prompt on your local disk, never touches the cloud, and presents a clean two-pane UI for browsing, editing, tagging, and copying prompts quickly.

## Highlights
- Searchable prompt library with tag previews and recency sorting.
- Create or update prompts with a title, comma-separated tags, and the full prompt text.
- Copy prompt text to the clipboard, delete entries, and clear the form with one tap.
- Data persists in a JSON store under your home directory so you can back it up or sync manually if desired.

## Requirements
- Python 3.10 or newer with the standard library (no third-party packages required).
- A desktop environment that can display Tkinter windows (Windows, macOS, or Linux).

## Setup & Usage
1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/) if it is not already on your machine.
2. Open a terminal or PowerShell session in this project directory.
3. Run `python prompt_vault.py` (or `py prompt_vault.py`) to launch the app.
4. Type a title, tags, and the prompt text, then click **Save Prompt** (or press `Ctrl+S`) to store it.
5. Select prompts from the left column to edit, delete, or copy them.

## Data Location
Saved prompts are stored locally in:
```
~/.prompt-vault/prompts.json
```
You can safely back up, restore, or open that file in any text editor.

## Tips
- Use the search box to filter by title, body, or tags instantly.
- Tags are optional; leave the field empty to treat a prompt as untagged.
- The app automatically sorts prompts by the most recently updated so your freshest ideas stay on top.

