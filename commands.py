# commands.py (improved)
import os
import shlex
import psutil
import shutil
import glob
from typing import Tuple

def _expand_path(cwd: str, target: str) -> str:
    """Expand ~ and env vars and join relative paths to cwd, returning absolute path."""
    if target is None or target == "":
        return os.path.abspath(cwd)
    # allow env vars and ~
    expanded = os.path.expanduser(os.path.expandvars(target))
    if os.path.isabs(expanded):
        return os.path.abspath(expanded)
    return os.path.abspath(os.path.join(cwd, expanded))

def _human_size(nbytes: int) -> str:
    """Return human readable size like '12.3 MB'."""
    if nbytes is None:
        return "0 B"
    n = float(nbytes)
    for unit in ("B","KB","MB","GB","TB"):
        if n < 1024.0 or unit == "TB":
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

def run_command(command: str, cwd: str) -> Tuple[str, str]:
    """
    Execute a safe subset of shell-like commands.
    Returns (output_text, new_cwd).
    """
    # tokenization: keep quoted strings intact
    try:
        tokens = shlex.split(command)
    except Exception as e:
        return (f"parse error: {e}", cwd)

    if not tokens:
        return ("", cwd)

    cmd = tokens[0]

    # ---------- pwd ----------
    if cmd == "pwd":
        return (cwd, cwd)

    # ---------- ls ----------
    if cmd == "ls":
        # simple flag support: -a
        show_all = False
        targets = []
        for tok in tokens[1:]:
            if tok == "-a":
                show_all = True
            else:
                targets.append(tok)
        if not targets:
            targets = ["."]
        out_lines = []
        for t in targets:
            # support globs
            pattern = _expand_path(cwd, t)
            matches = []
            # if pattern contains shell-style glob chars, use glob
            if any(ch in t for ch in "*?[]"):
                matches = glob.glob(os.path.expanduser(os.path.expandvars(t)))
                # convert to absolute
                matches = [os.path.abspath(m) for m in matches]
            else:
                matches = [pattern]
            for m in matches:
                if not os.path.exists(m):
                    out_lines.append(f"ls: cannot access '{t}': No such file or directory")
                    continue
                if os.path.isdir(m):
                    try:
                        items = os.listdir(m)
                        if not show_all:
                            items = [it for it in items if not it.startswith('.')]
                        display = []
                        for n in sorted(items):
                            p = os.path.join(m, n)
                            display.append(n + ("/" if os.path.isdir(p) else ""))
                        header = f"{t}:" if len(matches) > 1 or len(targets) > 1 else ""
                        if header:
                            out_lines.append(header)
                        if display:
                            out_lines.extend(display)
                        else:
                            out_lines.append("(empty)")
                    except Exception as e:
                        out_lines.append(f"ls error: {e}")
                else:
                    # file
                    out_lines.append(os.path.basename(m))
        return ("\n".join(out_lines), cwd)

    # ---------- cd ----------
    if cmd == "cd":
        if len(tokens) < 2:
            return ("cd: missing argument", cwd)
        target = tokens[1]
        newpath = _expand_path(cwd, target)
        if os.path.isdir(newpath):
            return (f"Changed directory to {newpath}", newpath)
        else:
            return (f"cd: no such directory: {target}", cwd)

    # ---------- mkdir ----------
    if cmd == "mkdir":
        if len(tokens) < 2:
            return ("mkdir: missing folder name", cwd)
        folder = _expand_path(cwd, tokens[1])
        try:
            os.makedirs(folder, exist_ok=True)
            rel = os.path.relpath(folder, cwd)
            return (f"Folder created: {rel}", cwd)
        except Exception as e:
            return (f"mkdir error: {e}", cwd)

    # ---------- rm (supports -r, -f, -rf) ----------
    if cmd == "rm":
        flags = [t for t in tokens[1:] if t.startswith("-")]
        args = [t for t in tokens[1:] if not t.startswith("-")]
        recursive = any("r" in f for f in flags)
        force = any("f" in f for f in flags)

        if not args:
            return ("rm: missing target name", cwd)

        target_raw = args[0]
        target = _expand_path(cwd, target_raw)

        if not os.path.exists(target):
            return ("rm: no such file or directory", cwd)

        try:
            if os.path.isdir(target):
                if recursive:
                    try:
                        shutil.rmtree(target)
                        return (f"Removed directory recursively: {target_raw}", cwd)
                    except Exception as e:
                        if force:
                            try:
                                shutil.rmtree(target, ignore_errors=True)
                                return (f"Removed directory recursively (force): {target_raw}", cwd)
                            except Exception as e2:
                                return (f"rm error: {e2}", cwd)
                        return (f"rm error: {e}", cwd)
                else:
                    try:
                        os.rmdir(target)
                        return (f"Removed directory: {target_raw}", cwd)
                    except Exception as e:
                        return (f"rm error: {e}", cwd)
            else:
                # file
                try:
                    os.remove(target)
                    return (f"Removed file: {target_raw}", cwd)
                except Exception as e:
                    if force:
                        try:
                            os.remove(target)
                            return (f"Removed file (force): {target_raw}", cwd)
                        except Exception as e2:
                            return (f"rm error: {e2}", cwd)
                    return (f"rm error: {e}", cwd)
        except Exception as e:
            return (f"rm error: {e}", cwd)

    # ---------- cat ----------
    if cmd == "cat":
        if len(tokens) < 2:
            return ("cat: missing filename", cwd)
        target = _expand_path(cwd, tokens[1])
        try:
            with open(target, "r", encoding="utf-8") as f:
                return (f.read(), cwd)
        except Exception as e:
            return (f"cat error: {e}", cwd)

    # ---------- touch ----------
    if cmd == "touch":
        if len(tokens) < 2:
            return ("touch: missing filename", cwd)
        target = _expand_path(cwd, tokens[1])
        try:
            # create empty file or update mtime
            with open(target, "a", encoding="utf-8"):
                os.utime(target, None)
            return (f"Touched: {tokens[1]}", cwd)
        except Exception as e:
            return (f"touch error: {e}", cwd)

    # ---------- echo (supports redirection with >) ----------
    if cmd == "echo":
        # look for '>' redirection
        if ">" in tokens:
            try:
                idx = tokens.index(">")
                text_parts = tokens[1:idx]
                filename = tokens[idx+1] if idx+1 < len(tokens) else None
                if filename is None:
                    return ("echo: no file specified for redirection", cwd)
                text = " ".join(text_parts)
                target = _expand_path(cwd, filename)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(text + "\n")
                return (f"Wrote to {filename}", cwd)
            except Exception as e:
                return (f"echo error: {e}", cwd)
        else:
            # just return joined text
            return (" ".join(tokens[1:]), cwd)

    # ---------- status ----------
    if cmd == "status":
        try:
            cpu = psutil.cpu_percent(interval=0.2)
            mem = psutil.virtual_memory()
            lines = [
                f"CPU: {cpu:.1f}%",
                f"Memory: {mem.percent:.1f}% used ({_human_size(mem.used)} / {_human_size(mem.total)})",
                f"Processes: {len(psutil.pids())}"
            ]
            return ("\n".join(lines), cwd)
        except Exception as e:
            return (f"status error: {e}", cwd)

    # ---------- mv ----------
    if cmd == "mv":
        if len(tokens) < 3:
            return ("mv: usage: mv <src> <dst>", cwd)
        src = _expand_path(cwd, tokens[1])
        dst_raw = tokens[2]
        dst = _expand_path(cwd, dst_raw)
        try:
            # if dst is an existing directory, move src inside it
            if os.path.isdir(dst):
                dst = os.path.join(dst, os.path.basename(src))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return (f"Moved {tokens[1]} -> {tokens[2]}", cwd)
        except Exception as e:
            return (f"mv error: {e}", cwd)

    # ---------- cp ----------
    if cmd == "cp":
        if len(tokens) < 3:
            return ("cp: usage: cp <src> <dst>", cwd)
        src = _expand_path(cwd, tokens[1])
        dst_raw = tokens[2]
        dst = _expand_path(cwd, dst_raw)
        try:
            if os.path.isdir(src):
                # if destination exists and is a dir, copy inside it
                if os.path.isdir(dst):
                    final_dst = os.path.join(dst, os.path.basename(src))
                    if os.path.exists(final_dst):
                        shutil.rmtree(final_dst)
                    shutil.copytree(src, final_dst)
                else:
                    # copy entire tree to dst (dst may or may not exist)
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
            else:
                # src is file
                if os.path.isdir(dst):
                    final_dst = os.path.join(dst, os.path.basename(src))
                    shutil.copy2(src, final_dst)
                else:
                    # ensure parent dir exists
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
            return (f"Copied {tokens[1]} -> {tokens[2]}", cwd)
        except Exception as e:
            return (f"cp error: {e}", cwd)

    return (f"Unknown command: {cmd}", cwd)
