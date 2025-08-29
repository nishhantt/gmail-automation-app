import tkinter as tk
from tkinter import ttk, messagebox
from gmail_handler import get_service, apply_rules
import json
import os
import sys

# ---- Handle file paths for exe or script ----
if getattr(sys, 'frozen', False):  # Running as exe
    APP_DIR = os.path.dirname(sys.executable)
else:  # Running as script
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

RULES_FILE = os.path.join(APP_DIR, "rules.json")
LOG_FILE = os.path.join(APP_DIR, "actions.log")

# ---- Rules Functions ----
def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"rules": [], "default_action": "keep"}

def save_rules(rules_data):
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(rules_data, f, indent=4)
    refresh_table()

def add_rule():
    pattern = entry_email.get().strip()
    match_type = combo_match.get()
    action = combo_action.get()
    if not pattern or not action:
        messagebox.showerror("Error", "Please enter an email/domain and select an action.")
        return
    rules_data = load_rules()
    for rule in rules_data["rules"]:
        if rule["pattern"] == pattern and rule["match_type"] == match_type:
            messagebox.showwarning("Warning", "Rule already exists.")
            return
    rules_data["rules"].append({"pattern": pattern, "match_type": match_type, "action": action})
    save_rules(rules_data)
    entry_email.delete(0, tk.END)

def delete_rule():
    selected = table.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select a rule to delete.")
        return
    rules_data = load_rules()
    for sel in selected:
        index = int(table.item(sel, "text"))
        del rules_data["rules"][index]
    save_rules(rules_data)

def edit_rule():
    selected = table.selection()
    if not selected or len(selected) != 1:
        messagebox.showwarning("Warning", "Select exactly one rule to edit.")
        return
    index = int(table.item(selected[0], "text"))
    rules_data = load_rules()
    rule = rules_data["rules"][index]
    entry_email.delete(0, tk.END)
    entry_email.insert(0, rule["pattern"])
    combo_match.set(rule["match_type"])
    combo_action.set(rule["action"])
    del rules_data["rules"][index]
    save_rules(rules_data)

def refresh_table():
    for row in table.get_children():
        table.delete(row)
    rules_data = load_rules()
    for i, rule in enumerate(rules_data["rules"]):
        table.insert("", "end", text=str(i), values=(rule["pattern"], rule["match_type"], rule["action"]))

# ---- Gmail Automation Functions ----
def run_dry_run():
    service = get_service()
    rules_data = load_rules()
    apply_rules(service, rules_data, dry_run=True, log_file=LOG_FILE)
    messagebox.showinfo("Dry Run Complete", f"Check {LOG_FILE} for results.")

def run_apply():
    service = get_service()
    rules_data = load_rules()
    apply_rules(service, rules_data, dry_run=False, log_file=LOG_FILE)
    messagebox.showinfo("Actions Applied", f"Check {LOG_FILE} for results.")

# ---- UI Setup ----
root = tk.Tk()
root.title("Gmail Automation Desktop App")

# --- Rules Manager Frame ---
frame_rules = tk.LabelFrame(root, text="Rules Manager", padx=5, pady=5)
frame_rules.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

tk.Label(frame_rules, text="Email / Domain / Regex:").grid(row=0, column=0, padx=5, pady=5)
entry_email = tk.Entry(frame_rules, width=40)
entry_email.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_rules, text="Match Type:").grid(row=1, column=0, padx=5, pady=5)
combo_match = ttk.Combobox(frame_rules, values=["exact", "domain", "regex"], state="readonly")
combo_match.current(0)
combo_match.grid(row=1, column=1, padx=5, pady=5)

tk.Label(frame_rules, text="Action:").grid(row=2, column=0, padx=5, pady=5)
combo_action = ttk.Combobox(frame_rules, values=["keep", "delete", "archive", "move_to_spam"], state="readonly")
combo_action.current(0)
combo_action.grid(row=2, column=1, padx=5, pady=5)

btn_add = tk.Button(frame_rules, text="Add Rule", command=add_rule)
btn_add.grid(row=3, column=0, pady=5)

btn_edit = tk.Button(frame_rules, text="Edit Selected", command=edit_rule)
btn_edit.grid(row=3, column=1, pady=5)

btn_delete = tk.Button(frame_rules, text="Delete Selected", command=delete_rule)
btn_delete.grid(row=4, column=0, columnspan=2, pady=5)

# Table to display rules
columns = ("pattern", "match_type", "action")
table = ttk.Treeview(frame_rules, columns=columns, show="headings")
table.heading("pattern", text="Email / Domain / Regex")
table.heading("match_type", text="Match Type")
table.heading("action", text="Action")
table.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

refresh_table()

# --- Automation Frame ---
frame_run = tk.LabelFrame(root, text="Run Gmail Automation", padx=5, pady=5)
frame_run.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

btn_dry_run = tk.Button(frame_run, text="Dry Run", width=20, command=run_dry_run)
btn_dry_run.grid(row=0, column=0, padx=5, pady=5)

btn_apply = tk.Button(frame_run, text="Apply Actions", width=20, command=run_apply)
btn_apply.grid(row=0, column=1, padx=5, pady=5)

root.mainloop()
