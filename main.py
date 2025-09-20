# main.py
"""
Python-Based Command Terminal (MVP + Add-ons)
Entry point required by the assignment.
"""

import os
import readline
from commands import run_command
from nlp import parse_nl_command

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

def completer(text, state):
    options = [c for c in ['ls','cd','pwd','mkdir','rm','cat','status','history','help','exit','mv','cp'] if c.startswith(text)]
    if state < len(options):
        return options[state]
    return None

def print_help():
    print("""
Available commands:
  ls [path]        - list files
  pwd              - print working directory
  cd <dir>         - change directory
  mkdir <name>     - create directory
  rm <name>        - remove file or empty directory
  cat <file>       - show file contents
  status           - show CPU & memory usage
  history          - show past commands in this session
  mv <src> <dst>   - move file/dir
  cp <src> <dst>   - copy file/dir
  help             - this help
  exit             - quit

You can also type natural language like:
  "create a folder test"
  "delete file a.txt"
  "move file a.txt to dir backup"
""")

def main():
    os.chdir(ROOT_DIR)  # sandbox to project folder
    history = []

    try:
        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")
    except Exception:
        pass

    print("🚀 Python-Based Terminal (MVP + Add-ons)")
    print(f"Working root directory (sandboxed): {ROOT_DIR}")
    print("Type 'help' for commands, or 'exit' to quit.\n")

    while True:
        try:
            prompt = f"{os.getcwd()} $ "
            raw = input(prompt).strip()
            if raw == "":
                continue

            history.append(raw)

            if raw.lower() == "exit":
                print("Goodbye 👋")
                break
            if raw.lower() == "help":
                print_help()
                continue
            if raw.lower() == "history":
                for i, h in enumerate(history, 1):
                    print(f"{i}: {h}")
                continue

            # Try NLP conversion for natural-language inputs
            nl_tokens = raw.lower().split()
            if any(w in nl_tokens for w in ["create","make","delete","remove","move","rename","copy","place","open","read"]):
                converted = parse_nl_command(raw)
                if converted:
                    print(f"[NLP] Interpreted as: {converted}")
                    raw = converted

            output, new_cwd = run_command(raw, os.getcwd())

            # enforce sandbox: do not allow escape from project root
            if new_cwd and not os.path.abspath(new_cwd).startswith(ROOT_DIR):
                print("❌ Operation would escape sandbox. Ignored.")
                continue

            if new_cwd and new_cwd != os.getcwd():
                os.chdir(new_cwd)

            if output:
                print(output)

        except KeyboardInterrupt:
            print("\nKeyboardInterrupt — type 'exit' to quit.")
        except EOFError:
            print("\nEOF received. Exiting.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
