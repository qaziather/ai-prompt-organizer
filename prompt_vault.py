from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

APP_NAME = "Prompt Vault"
STORE_PATH = Path.home() / ".prompt-vault" / "prompts.json"


@dataclass
class PromptEntry:
    id: str
    title: str
    body: str
    tags: list[str]
    created_at: str
    updated_at: str

    def matches(self, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        if q in self.title.lower() or q in self.body.lower():
            return True
        return any(q in tag.lower() for tag in self.tags)


class PromptStore:
    def __init__(self, path: Path):
        self.path = path
        self.prompts: list[PromptEntry] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.prompts = []
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            loaded = []
            for item in raw:
                if "id" in item and "title" in item and "body" in item:
                    loaded.append(
                        PromptEntry(
                            id=item.get("id", str(uuid.uuid4())),
                            title=item.get("title", ""),
                            body=item.get("body", ""),
                            tags=item.get("tags", []),
                            created_at=item.get("created_at", datetime.utcnow().isoformat()),
                            updated_at=item.get("updated_at", datetime.utcnow().isoformat()),
                        )
                    )
            self.prompts = sorted(loaded, key=lambda p: p.updated_at, reverse=True)
        except (json.JSONDecodeError, OSError):
            self.prompts = []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump([asdict(prompt) for prompt in self.prompts], handle, ensure_ascii=False, indent=2)

    def upsert(self, prompt: PromptEntry) -> None:
        for idx, existing in enumerate(self.prompts):
            if existing.id == prompt.id:
                self.prompts[idx] = prompt
                break
        else:
            self.prompts.append(prompt)
        self.prompts.sort(key=lambda p: p.updated_at, reverse=True)

    def delete(self, prompt_id: str) -> None:
        self.prompts = [prompt for prompt in self.prompts if prompt.id != prompt_id]


class PromptVaultApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("1024x640")
        self.root.minsize(860, 520)
        self.root.configure(bg="#0f172a")
        self.store = PromptStore(STORE_PATH)
        self.visible_prompts: list[PromptEntry] = []
        self.selected_prompt_id: str | None = None
        self.status_clear_id = None

        self.title_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready to save prompts locally.")

        self._setup_style()
        self._build_layout()
        self._bind_events()
        self._refresh_prompt_list()

    def _setup_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "TLabel",
            background="#0f172a",
            foreground="#f8fafc",
            font=("Segoe UI", 11),
        )
        style.configure(
            "Header.TLabel",
            font=("Segoe UI Semibold", 16),
            foreground="#e0e7ff",
        )
        style.configure(
            "TEntry",
            fieldbackground="#0b1120",
            foreground="#f8fafc",
            bordercolor="#1e293b",
            padding=6,
            relief="flat",
        )
        style.configure(
            "Accent.TButton",
            font=("Segoe UI Semibold", 10),
            foreground="#f1f5f9",
            background="#6366f1",
            bordercolor="#a5b4fc",
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#7c3aed"), ("disabled", "#4c1d95")],
        )

    def _build_layout(self) -> None:
        main_frame = tk.Frame(self.root, bg="#0f172a")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=1, uniform="panels")
        main_frame.columnconfigure(1, weight=2, uniform="panels")

        list_frame = tk.Frame(main_frame, bg="#0f172a")
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        list_frame.rowconfigure(2, weight=1)

        ttk.Label(list_frame, text="Prompt Library", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        search_entry = ttk.Entry(list_frame, textvariable=self.search_var)
        search_entry.grid(row=1, column=0, sticky="ew", pady=10)

        self.prompt_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 11),
            bg="#0b1220",
            fg="#f8fafc",
            selectbackground="#334155",
            bd=0,
            highlightthickness=0,
            activestyle="none",
            relief="flat",
        )
        self.prompt_listbox.grid(row=2, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, command=self.prompt_listbox.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.prompt_listbox.configure(yscrollcommand=scrollbar.set)

        form_frame = tk.Frame(main_frame, bg="#0f172a")
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.rowconfigure(3, weight=1)

        ttk.Label(form_frame, text="Prompt Details", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(form_frame, text="Title").grid(row=1, column=0, sticky="w", pady=(12, 4))
        self.title_entry = ttk.Entry(form_frame, textvariable=self.title_var)
        self.title_entry.grid(row=2, column=0, sticky="ew")

        ttk.Label(form_frame, text="Tags (comma separated)").grid(row=3, column=0, sticky="w", pady=(12, 4))
        self.tags_entry = ttk.Entry(form_frame, textvariable=self.tags_var)
        self.tags_entry.grid(row=4, column=0, sticky="ew")

        ttk.Label(form_frame, text="Prompt Text").grid(row=5, column=0, sticky="w", pady=(12, 4))
        self.body_text = tk.Text(
            form_frame,
            bg="#031129",
            fg="#f8fafc",
            insertbackground="#f8fafc",
            relief="flat",
            wrap="word",
            font=("Segoe UI", 11),
            height=12,
        )
        self.body_text.grid(row=6, column=0, sticky="nsew")

        button_frame = tk.Frame(form_frame, bg="#0f172a")
        button_frame.grid(row=7, column=0, pady=18, sticky="ew")
        button_frame.columnconfigure((0, 1, 2), weight=1)

        self.save_button = ttk.Button(button_frame, text="Save Prompt", style="Accent.TButton", command=self.save_prompt)
        self.save_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(button_frame, text="Copy Text", command=self.copy_to_clipboard).grid(row=0, column=1, sticky="ew", padx=8)
        self.delete_button = ttk.Button(button_frame, text="Delete Prompt", command=self.delete_prompt, state="disabled")
        self.delete_button.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        ttk.Button(form_frame, text="Clear Form", command=self.clear_form).grid(row=8, column=0, sticky="ew")

        self.status_label = ttk.Label(self.root, textvariable=self.status_var)
        self.status_label.pack(fill="x", padx=20, pady=(0, 10))

    def _bind_events(self) -> None:
        self.prompt_listbox.bind("<<ListboxSelect>>", self._on_prompt_select)
        self.search_var.trace_add("write", lambda *_: self._refresh_prompt_list())
        self.root.bind("<Control-s>", lambda event: (self.save_prompt(), "break"))

    def _refresh_prompt_list(self) -> None:
        query = self.search_var.get().strip()
        self.visible_prompts = [prompt for prompt in self.store.prompts if prompt.matches(query)]
        self.prompt_listbox.delete(0, tk.END)
        for prompt in self.visible_prompts:
            tags = ", ".join(prompt.tags) if prompt.tags else "untagged"
            label = f"{prompt.title} · {tags}"
            self.prompt_listbox.insert(tk.END, label)
        if not self.visible_prompts:
            self.clear_form()
            self.delete_button.state(["disabled"])
        self.status_var.set(f"{len(self.visible_prompts)} prompts found.")

    def _on_prompt_select(self, event: tk.Event) -> None:
        selection = self.prompt_listbox.curselection()
        if not selection:
            return
        prompt = self.visible_prompts[selection[0]]
        self.selected_prompt_id = prompt.id
        self.title_var.set(prompt.title)
        self.tags_var.set(", ".join(prompt.tags))
        self.body_text.delete("1.0", tk.END)
        self.body_text.insert("1.0", prompt.body)
        self.delete_button.state(["!disabled"])
        self.save_button.config(text="Update Prompt")
        self.set_status(f"Editing {prompt.title}")

    def _build_prompt_payload(self) -> PromptEntry | None:
        title = self.title_var.get().strip()
        body = self.body_text.get("1.0", tk.END).strip()
        if not title or not body:
            messagebox.showwarning("Incomplete data", "Please add both a title and the prompt text.")
            return None
        tags = [tag.strip() for tag in self.tags_var.get().split(",") if tag.strip()]
        now = datetime.utcnow().isoformat()
        prompt_id = self.selected_prompt_id or str(uuid.uuid4())
        created_time = now if self.selected_prompt_id is None else next(
            (p.created_at for p in self.store.prompts if p.id == self.selected_prompt_id),
            now,
        )
        return PromptEntry(
            id=prompt_id,
            title=title,
            body=body,
            tags=tags,
            created_at=created_time,
            updated_at=now,
        )

    def save_prompt(self) -> None:
        payload = self._build_prompt_payload()
        if not payload:
            return
        self.store.upsert(payload)
        self.store.save()
        self._refresh_prompt_list()
        self.selected_prompt_id = payload.id
        self.save_button.config(text="Update Prompt")
        self.set_status(f"Saved “{payload.title}”")

    def delete_prompt(self) -> None:
        if not self.selected_prompt_id:
            return
        result = messagebox.askyesno("Delete prompt", "Are you sure you want to delete this prompt?")
        if not result:
            return
        self.store.delete(self.selected_prompt_id)
        self.store.save()
        self.clear_form()
        self._refresh_prompt_list()
        self.set_status("Prompt deleted.")

    def copy_to_clipboard(self) -> None:
        body = self.body_text.get("1.0", tk.END).strip()
        if not body:
            self.set_status("No prompt text to copy.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(body)
        self.set_status("Prompt copied to clipboard.")

    def clear_form(self) -> None:
        self.selected_prompt_id = None
        self.title_var.set("")
        self.tags_var.set("")
        self.body_text.delete("1.0", tk.END)
        self.save_button.config(text="Save Prompt")
        self.delete_button.state(["disabled"])
        self.set_status("Ready for a new prompt.")

    def set_status(self, text: str) -> None:
        self.status_var.set(text)
        if self.status_clear_id:
            self.root.after_cancel(self.status_clear_id)
        self.status_clear_id = self.root.after(4000, lambda: self.status_var.set("Ready to save prompts locally."))

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    PromptVaultApp().run()


if __name__ == "__main__":
    main()
