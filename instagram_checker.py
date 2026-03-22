#!/usr/bin/env python3
"""
Instagram Follow-back Checker
==============================
Paste your Followers and Following lists (copied from Instagram desktop).
Shows who doesn't follow you back — with both display name AND username.

Run:  python instagram_checker.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _is_username(s: str) -> bool:
    """Instagram usernames: 1-30 chars, only letters/digits/dots/underscores, no spaces."""
    return bool(re.fullmatch(r'[\w.]{1,30}', s))

def parse_accounts(text: str) -> dict:
    
    # --- Step 1: strip junk lines ---
    _SKIP_EXACT = {
        'search', '·', '•', '-', 'follow', 'following', 'followers',
        'requested', 'remove', 'unfollow', 'message', 'suggested',
        'verified', 'restricted',
    }
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.lower() in _SKIP_EXACT:
            continue
        if re.search(r"'s profile picture", line, re.IGNORECASE):
            continue
        if re.fullmatch(r'[\d,\.\s]+', line):   # pure numbers / counts
            continue
        lines.append(line)

    # --- Step 2: walk lines, pair username → optional display name ---
    accounts = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if _is_username(line):
            username = line.lower()
            display = None
            # Next line is a display name if it cannot be a username itself
            if i + 1 < len(lines) and not _is_username(lines[i + 1]):
                display = lines[i + 1]
                i += 2
            else:
                i += 1
            if username not in accounts:
                accounts[username] = display or username
        else:
            # Non-username line with no prior username to attach to — skip
            i += 1

    return accounts

# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Instagram Follow-back Checker")
        self.resizable(True, True)
        self.minsize(900, 600)
        self.configure(bg="#802419")
        self._build()

    def _build(self):
        pad = dict(padx=8, pady=6)
        style = ttk.Style(self)

        info = ttk.Label(
            self,
            text=(
                "HOW TO COPY FROM INSTAGRAM (desktop browser):\n"
                "Open your profile → Followers or Following → Hold and select from the top to the bottom or Ctrl+A → Ctrl+C → paste below."
            ),
            justify="center", foreground="#555",
        )
        info.grid(row=0, column=0, columnspan=3, sticky="ew", padx=12, pady=(10, 2))

        # Left: followers
        lf = ttk.LabelFrame(self, text="Your FOLLOWERS  (people who follow you)")
        lf.grid(row=1, column=0, sticky="nsew", **pad)
        self._followers_txt = self._make_textbox(lf)

        # Right: following
        rf = ttk.LabelFrame(self, text="Your FOLLOWING  (people you follow)")
        rf.grid(row=1, column=2, sticky="nsew", **pad)
        self._following_txt = self._make_textbox(rf)

        # Middle buttons
        mid = ttk.Frame(self)
        mid.grid(row=1, column=1, sticky="ns", padx=4)
        ttk.Button(mid, text="▶  Check",      command=self._check,  width=14).pack(pady=(60, 8))
        ttk.Button(mid, text="⟳  Clear all",  command=self._clear,  width=14).pack(pady=4)
        ttk.Button(mid, text="Load file\n(followers)", command=lambda: self._load_file(self._followers_txt), width=14).pack(pady=4)
        ttk.Button(mid, text="Load file\n(following)", command=lambda: self._load_file(self._following_txt), width=14).pack(pady=4)

        # Results
        rframe = ttk.LabelFrame(self, text="Not following you back  —  Name  |  @username")
        rframe.grid(row=2, column=0, columnspan=3, sticky="nsew", **pad)

        self._result_txt = tk.Text(
            rframe, height=12, wrap="word",
            font=("Consolas", 10), bg="#1e1e1e", fg="#e8e8e8",
            insertbackground="white", relief="flat", state="disabled",
        )
        sb = ttk.Scrollbar(rframe, command=self._result_txt.yview)
        self._result_txt.configure(yscrollcommand=sb.set)
        self._result_txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._status = ttk.Label(self, text="", foreground="#666")
        self._status.grid(row=3, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 6))

    def _make_textbox(self, parent) -> tk.Text:
        f = ttk.Frame(parent)
        f.pack(fill="both", expand=True, padx=4, pady=4)
        txt = tk.Text(f, wrap="none", font=("Consolas", 9), bg="#fafafa", relief="flat")
        sby = ttk.Scrollbar(f, command=txt.yview)
        sbx = ttk.Scrollbar(f, orient="horizontal", command=txt.xview)
        txt.configure(yscrollcommand=sby.set, xscrollcommand=sbx.set)
        txt.grid(row=0, column=0, sticky="nsew")
        sby.grid(row=0, column=1, sticky="ns")
        sbx.grid(row=1, column=0, sticky="ew")
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)
        return txt

    def _check(self):
        followers_raw = self._followers_txt.get("1.0", "end")
        following_raw = self._following_txt.get("1.0", "end")

        followers  = parse_accounts(followers_raw)   # {username: display_name}
        following  = parse_accounts(following_raw)

        if not followers and not following:
            messagebox.showwarning("Empty", "Please paste your Followers and Following lists first.")
            return

        not_back = {u: n for u, n in following.items() if u not in followers}

        self._result_txt.configure(state="normal")
        self._result_txt.delete("1.0", "end")

        if not_back:
            lines = []
            for username, display in sorted(not_back.items(), key=lambda x: x[0]):
                if display and display.lower() != username:
                    lines.append(f"{display:<30}  @{username}")
                else:
                    lines.append(f"@{username}")
            self._result_txt.insert("end", "\n".join(lines))
        else:
            self._result_txt.insert("end", "Everyone you follow also follows you back!")

        if self._debug_var.get():
            self._result_txt.insert("end", "\n\n--- DEBUG: parsed followers ---\n")
            for u, d in sorted(followers.items()):
                self._result_txt.insert("end", f"  {d:<30}  @{u}\n")
            self._result_txt.insert("end", "\n--- DEBUG: parsed following ---\n")
            for u, d in sorted(following.items()):
                self._result_txt.insert("end", f"  {d:<30}  @{u}\n")

        self._result_txt.configure(state="disabled")

        self._status.configure(
            text=(
                f"Followers parsed: {len(followers)}   |   "
                f"Following parsed: {len(following)}   |   "
                f"Not following back: {len(not_back)}"
            )
        )

    def _clear(self):
        for txt in (self._followers_txt, self._following_txt):
            txt.delete("1.0", "end")
        self._result_txt.configure(state="normal")
        self._result_txt.delete("1.0", "end")
        self._result_txt.configure(state="disabled")
        self._status.configure(text="")

    def _load_file(self, target):
        path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                target.delete("1.0", "end")
                target.insert("1.0", f.read())


if __name__ == "__main__":
    app = App()
    app.mainloop()
