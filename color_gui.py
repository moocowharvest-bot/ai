#!/usr/bin/env python3
"""
color_gui.py

Simple Tkinter GUI wrapper around convert_colors.py.
Loads text, replaces color words randomly (preserving case), shows output
and copies the result to the clipboard.

Usage:
  python color_gui.py

Requires: Python 3, convert_colors.py in the same folder.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import random
import sys
from pathlib import Path

try:
    from convert_colors import convert_colors, COLORS, convert_hair, HAIR
except Exception as e:
    print("Failed to import convert_colors.py:", e)
    sys.exit(1)


def save_output():
    out = output_text.get('1.0', tk.END)
    path = filedialog.asksaveasfilename(title="Save output", defaultextension='.txt', filetypes=[('Text','*.txt'), ('All','*.*')])
    if not path:
        return
    Path(path).write_text(out, encoding='utf-8')
    status_var.set(f"Saved: {Path(path).name}")


def load_file():
    path = filedialog.askopenfilename(title="Open text file", filetypes=[('Text','*.txt'), ('All','*.*')])
    if not path:
        return
    txt = Path(path).read_text(encoding='utf-8')
    input_text.delete('1.0', tk.END)
    input_text.insert(tk.END, txt)
    status_var.set(f"Loaded: {Path(path).name}")


def convert_and_copy():
    txt = input_text.get('1.0', tk.END)
    if not txt.strip():
        messagebox.showinfo("No text", "Please enter or load some text to convert.")
        return

    seed_str = seed_entry.get().strip()
    rng = random.Random(int(seed_str)) if seed_str.isdigit() else random.Random()

    out, counts = convert_colors(txt, rng, colors=COLORS)
    newout, counts = convert_hair(out, rng, hair=HAIR)
    output_text.delete('1.0', tk.END)
    output_text.insert(tk.END, newout)

    # copy to clipboard
    root.clipboard_clear()
    root.clipboard_append(newout)

    total = sum(counts.values())
    if total:
        status_var.set(f"Replacements: {total} — Copied to clipboard")
    else:
        status_var.set("No color words found — Copied to clipboard")


def clear_all():
    input_text.delete('1.0', tk.END)
    output_text.delete('1.0', tk.END)
    status_var.set('Cleared')


def build_ui():
    global root, input_text, output_text, seed_entry, status_var
    root = tk.Tk()
    root.title('Color Replacer')
    root.geometry('900x700')

    # Dark theme colors
    DARK_BG = '#1e1e1e'
    DARK_FG = '#dcdcdc'
    PANEL_BG = '#252526'
    BUTTON_BG = '#2d2d2d'
    BUTTON_FG = '#ffffff'
    INPUT_BG = '#1e1e1e'
    INPUT_FG = '#d4d4d4'
    INSERT_COLOR = '#ffffff'
    SELECT_BG = '#264f78'

    root.configure(bg=DARK_BG)

    frm = tk.Frame(root, bg=PANEL_BG)
    frm.pack(fill=tk.BOTH, expand=True)

    top_frame = tk.Frame(frm, bg=PANEL_BG)
    top_frame.pack(fill=tk.BOTH, expand=True)

    lbl_in = tk.Label(top_frame, text='Input Text', bg=PANEL_BG, fg=DARK_FG)
    lbl_in.pack(anchor='w')
    input_text = tk.Text(top_frame, wrap='word', height=15, bg=INPUT_BG, fg=INPUT_FG, insertbackground=INSERT_COLOR, selectbackground=SELECT_BG)
    input_text.pack(fill=tk.BOTH, expand=True)

    controls = tk.Frame(frm, bg=PANEL_BG)
    controls.pack(fill=tk.X)

    tk.Button(controls, text='Load...', command=load_file, bg=BUTTON_BG, fg=BUTTON_FG, activebackground=BUTTON_BG).pack(side=tk.LEFT, padx=4, pady=6)
    tk.Button(controls, text='Convert & Copy', command=convert_and_copy, bg=BUTTON_BG, fg=BUTTON_FG, activebackground=BUTTON_BG).pack(side=tk.LEFT, padx=4)
    tk.Button(controls, text='Save Output...', command=save_output, bg=BUTTON_BG, fg=BUTTON_FG, activebackground=BUTTON_BG).pack(side=tk.LEFT, padx=4)
    tk.Button(controls, text='Clear', command=clear_all, bg=BUTTON_BG, fg=BUTTON_FG, activebackground=BUTTON_BG).pack(side=tk.LEFT, padx=4)

    tk.Label(controls, text='Seed:', bg=PANEL_BG, fg=DARK_FG).pack(side=tk.LEFT, padx=(12,2))
    seed_entry = tk.Entry(controls, width=10, bg=INPUT_BG, fg=INPUT_FG, insertbackground=INSERT_COLOR)
    seed_entry.pack(side=tk.LEFT)

    tk.Label(controls, text='(optional)', bg=PANEL_BG, fg=DARK_FG).pack(side=tk.LEFT, padx=(4,0))


    lbl_out = tk.Label(frm, text='Output', bg=PANEL_BG, fg=DARK_FG)
    lbl_out.pack(anchor='w')
    output_text = tk.Text(frm, wrap='word', height=15, bg=INPUT_BG, fg=INPUT_FG, insertbackground=INSERT_COLOR, selectbackground=SELECT_BG)
    output_text.pack(fill=tk.BOTH, expand=True)

    status_var = tk.StringVar()
    status_var.set('Ready')
    status = tk.Label(root, textvariable=status_var, anchor='w', bg=PANEL_BG, fg=DARK_FG)
    status.pack(fill=tk.X, side=tk.BOTTOM)

    def on_ctrl_enter(event=None):
        convert_and_copy()
        return 'break'

    root.bind('<Control-Return>', on_ctrl_enter)


if __name__ == '__main__':
    build_ui()
    root.mainloop()
