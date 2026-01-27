#!/usr/bin/env python3
import subprocess
import sys
import shlex
import os
import threading
import random
import re

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _pick_ai_binary():
    # On Windows, prefer the .exe produced by the MSVC build.
    candidates = [
        os.path.join(_BASE_DIR, "ai.exe"),
        os.path.join(_BASE_DIR, "ai"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return candidates[0]


AI_BIN = _pick_ai_binary()

def run_ai(timeout=30):
    try:
        if not os.path.isfile(AI_BIN):
            return (
                f"Error: {AI_BIN} not found.\n"
                "Build the Windows binary first (it should create ai.exe next to gui.py).\n"
            )
        env = os.environ.copy()
        env['NO_CLIPBOARD'] = '1'
        result = subprocess.run([AI_BIN], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, env=env, cwd=os.path.dirname(os.path.abspath(__file__)))
        if result.returncode != 0:
            return f"Error running {AI_BIN}: returncode={result.returncode}, stderr={result.stderr.decode('utf-8')}\n"
        return result.stdout.decode('utf-8')
    except subprocess.TimeoutExpired:
        return f"Error: {AI_BIN} timed out after {timeout}s\n"
    except OSError as e:
        # Common on Windows if you try to execute a non-Win32 binary.
        return (
            f"Error running {AI_BIN}: {e}\n"
            "If you see WinError 193, make sure you're running ai.exe (a Windows build), not a non-Windows binary.\n"
        )
    except Exception as e:
        return f"Error running {AI_BIN}: {e}\n"

# Non-GUI mode for testing: print output and exit
if __name__ == '__main__':
    if '--generate' in sys.argv:
        print(run_ai())
        sys.exit(0)

    try:
        import tkinter as tk
        from tkinter.scrolledtext import ScrolledText
        from tkinter import messagebox
    except Exception as e:
        print('tkinter not available:', e)
        sys.exit(1)

    try:
        from convert_colors import (
            convert_colors,
            COLORS,
            convert_hair,
            HAIR,
            convert_style,
            STYLE,
            convert_material,
            MATERIAL,
            convert_camera,
            CAMERA_ANGLES,
            convert_clothes,
            UPPER,
            LOWER,
        )
    except Exception:
        convert_colors = None
        COLORS = None
        convert_hair = None
        HAIR = None
        convert_style = None
        STYLE = None
        convert_material = None
        MATERIAL = None
        convert_camera = None
        CAMERA_ANGLES = None
        convert_clothes = None
        UPPER = None
        LOWER = None

    root = tk.Tk()
    root.title('AI Generator')
    # Fit four large square buttons side-by-side, with labels underneath
    width = 880
    height = 300
    root.geometry(f'{width}x{height}')

    # Dark theme palette
    DARK_BG = '#1e1e1e'
    DARK_FG = '#dcdcdc'
    PANEL_BG = '#252526'
    BUTTON_BG = '#2d2d2d'
    BUTTON_FG = '#ffffff'

    root.configure(bg=DARK_BG)

    # (No special WM tweaks — use default window behavior)

    # Use only a single large square button centered in the window.
    # The button shows a play icon (Unicode) instead of text.
    play_icon = '\u25B6'  # ▶
    redo_icon = '\u27F3'  # ⟳

    last_output = {'text': ''}

    def generate():
        # Visual feedback: disable and show a spinner-like text
        btn.config(state='disabled', text='...', bg='#FFA000')

        def worker():
            output = run_ai()

            last_output['text'] = output

            def finish():
                try:
                    root.clipboard_clear()
                    root.clipboard_append(output)
                    # success visual
                    btn.config(text=play_icon, bg='#4CAF50')
                except Exception:
                    # failure visual
                    btn.config(text=play_icon, bg='#D32F2F')
                btn.config(state='normal')

            root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def replace_colors_and_copy():
        if convert_colors is None or convert_hair is None or convert_style is None or convert_material is None:
            messagebox.showerror(
                'Missing converter',
                'convert_colors.py could not be imported, so color replacement is unavailable.',
            )
            return

        # Prefer current clipboard contents; fall back to the last generated output.
        try:
            txt = root.clipboard_get()
        except Exception:
            txt = ''

        if not (txt or '').strip():
            txt = last_output.get('text') or ''

        if not txt:
            messagebox.showinfo('No text', 'Generate text first (or copy text to clipboard), then try again.')
            return

        replace_btn.config(state='disabled', text='...', bg='#FFA000')

        def worker():
            rng = random.Random()
            out, _counts = convert_colors(txt, rng, colors=COLORS)
            newout, _counts2 = convert_hair(out, rng, hair=HAIR)
            newerout, _counts2 = convert_style(newout, rng, style=STYLE)
            newestout, _counts2 = convert_material(newerout, rng, material=MATERIAL)

            def finish():
                try:
                    root.clipboard_clear()
                    root.clipboard_append(newestout)
                    replace_btn.config(text=redo_icon, bg='#4CAF50')
                except Exception:
                    replace_btn.config(text=redo_icon, bg='#D32F2F')
                replace_btn.config(state='normal')

            root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def randomize_camera_and_copy():
        if convert_camera is None:
            messagebox.showerror(
                'Missing converter',
                'convert_colors.py could not be imported, so camera randomization is unavailable.',
            )
            return

        def has_camera_angle(s: str) -> bool:
            # Known literal angles from C++
            if CAMERA_ANGLES:
                low = s.lower()
                for a in CAMERA_ANGLES:
                    if a and a.lower() in low:
                        return True
            # Dynamic C++ angle: (high angle shot:<float>)
            if re.search(r"\(high angle shot\s*:\s*\d+(?:\.\d+)?\)", s, flags=re.IGNORECASE):
                return True
            return False

        try:
            txt = root.clipboard_get()
        except Exception:
            txt = ''

        if not (txt or '').strip():
            messagebox.showinfo('No text', 'Copy a prompt to clipboard, then try again.')
            return

        camera_btn.config(state='disabled', text='...', bg='#FFA000')

        def worker():
            rng = random.Random()
            newtxt, did = convert_camera(txt, rng)

            def finish():
                try:
                    if not did:
                        if has_camera_angle(txt):
                            messagebox.showinfo(
                                'No valid replacement',
                                'A camera angle was detected, but no valid replacement was available for this prompt (getShot(output) constraints may restrict options).',
                            )
                        else:
                            messagebox.showinfo('No camera angle found', 'No recognizable camera angle was found to replace.')
                    root.clipboard_clear()
                    root.clipboard_append(newtxt)
                    camera_btn.config(text=redo_icon, bg='#4CAF50')
                except Exception:
                    camera_btn.config(text=redo_icon, bg='#D32F2F')
                camera_btn.config(state='normal')

            root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def randomize_clothes_and_copy():
        if convert_clothes is None:
            messagebox.showerror(
                'Missing converter',
                'convert_colors.py could not be imported, so clothes randomization is unavailable.',
            )
            return

        try:
            txt = root.clipboard_get()
        except Exception:
            txt = ''

        if not (txt or '').strip():
            txt = last_output.get('text') or ''

        if not txt:
            messagebox.showinfo('No text', 'Generate text first (or copy text to clipboard), then try again.')
            return

        clothes_btn.config(state='disabled', text='...', bg='#FFA000')

        def worker():
            rng = random.Random()
            newtxt, counts = convert_clothes(txt, rng, upper=UPPER, lower=LOWER)

            def finish():
                try:
                    root.clipboard_clear()
                    root.clipboard_append(newtxt)
                    clothes_btn.config(text=redo_icon, bg='#4CAF50')
                except Exception:
                    clothes_btn.config(text=redo_icon, bg='#D32F2F')
                clothes_btn.config(state='normal')

            root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    btn = tk.Button(
        root,
        text=play_icon,
        command=generate,
        font=('Helvetica', 72),
        bg='#4CAF50',
        fg=BUTTON_FG,
        activeforeground=BUTTON_FG,
        bd=0,
    )
    btn.place(relx=(1/8), rely=0.40, anchor='center', width=200, height=200)

    replace_btn = tk.Button(
        root,
        text=redo_icon,
        command=replace_colors_and_copy,
        font=('Helvetica', 72),
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        activebackground=BUTTON_BG,
        activeforeground=BUTTON_FG,
        bd=0,
    )
    replace_btn.place(relx=(3/8), rely=0.40, anchor='center', width=200, height=200)

    clothes_btn = tk.Button(
        root,
        text=redo_icon,
        command=randomize_clothes_and_copy,
        font=('Helvetica', 72),
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        activebackground=BUTTON_BG,
        activeforeground=BUTTON_FG,
        bd=0,
    )
    clothes_btn.place(relx=(5/8), rely=0.40, anchor='center', width=200, height=200)

    camera_btn = tk.Button(
        root,
        text=redo_icon,
        command=randomize_camera_and_copy,
        font=('Helvetica', 72),
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        activebackground=BUTTON_BG,
        activeforeground=BUTTON_FG,
        bd=0,
    )
    camera_btn.place(relx=(7/8), rely=0.40, anchor='center', width=200, height=200)

    gen_lbl = tk.Label(root, text='Generate Prompt', bg=DARK_BG, fg=DARK_FG)
    gen_lbl.place(relx=(1/8), rely=0.82, anchor='center')

    rand_lbl = tk.Label(root, text='Randomize Appearance', bg=DARK_BG, fg=DARK_FG)
    rand_lbl.place(relx=(3/8), rely=0.82, anchor='center')

    clothes_lbl = tk.Label(root, text='Randomize Clothes', bg=DARK_BG, fg=DARK_FG)
    clothes_lbl.place(relx=(5/8), rely=0.82, anchor='center')

    cam_lbl = tk.Label(root, text='Randomize Camera', bg=DARK_BG, fg=DARK_FG)
    cam_lbl.place(relx=(7/8), rely=0.82, anchor='center')

    root.mainloop()
