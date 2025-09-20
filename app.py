# app.py
import os
import gradio as gr
from commands import run_command
from nlp import parse_nl_command

ROOT = os.path.abspath(os.path.dirname(__file__))
START_CWD = ROOT  # sandbox starting directory

def sandboxed_run(cmd: str, cwd: str):
    """Run a command through your run_command and enforce sandbox root."""
    # Try NLP conversion first (keeps same behavior as your CLI)
    nl_tokens = (cmd or "").lower().split()
    if any(w in nl_tokens for w in ["create","make","delete","remove","move","rename","copy","place","open","read"]):
        converted = parse_nl_command(cmd)
        if converted:
            cmd = converted

    out, newcwd = run_command(cmd, cwd or START_CWD)

    # enforce sandbox to prevent escape
    if newcwd and not os.path.abspath(newcwd).startswith(ROOT):
        return "❌ Operation would escape sandbox. Ignored.", cwd or START_CWD

    # protect long outputs
    if out is None:
        out = ""

    return out, newcwd or cwd or START_CWD

def run_and_append(history: str, cmd: str, cwd: str):
    """Run command and append output to history box (simple single-session)."""
    if not cmd:
        return history, cwd
    out, newcwd = sandboxed_run(cmd, cwd)
    new_entry = f"$ {cmd}\n{out}\n\n"
    history = (history or "") + new_entry
    return history, newcwd

css = """
.output-area { font-family: monospace; white-space: pre-wrap; }
"""

with gr.Blocks(css=css, title="Python Terminal Demo") as demo:
    gr.Markdown("## Python Terminal (MVP)\nType `ls`, `cd`, `pwd`, `mkdir`, `rm`, `cat`, `status` or natural language like `create folder test`.")
    cwd_state = gr.State(START_CWD)

    with gr.Row():
        output = gr.Textbox(label="Terminal output", value="", interactive=False, lines=18, elem_id="terminal_output")
    with gr.Row():
        cmd = gr.Textbox(placeholder="e.g. ls, mkdir test, create folder demo", label="Command")
        run_btn = gr.Button("Run")

    run_btn.click(fn=run_and_append, inputs=[output, cmd, cwd_state], outputs=[output, cwd_state])
    cmd.submit(fn=run_and_append, inputs=[output, cmd, cwd_state], outputs=[output, cwd_state])

    gr.Markdown("**Important:** This demo runs inside the Space. It is sandboxed to the repository directory.")

if __name__ == "__main__":
    demo.launch()
