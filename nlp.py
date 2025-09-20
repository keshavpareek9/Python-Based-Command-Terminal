# nlp.py
import re
import os
from shlex import split as shlex_split

def _unquote(s: str):
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s

def parse_nl_command(text: str):
    """
    Natural-language -> command converter.
    Supports:
      - create/make folder|directory NAME
      - delete/remove file|folder|directory NAME
      - move/copy SOURCE to DEST
      - read/open/show file NAME
    """
    t = text.strip()

    try:
        toks = shlex_split(t)
        lower = " ".join([w.lower() for w in toks])
    except Exception:
        lower = t.lower()
        toks = t.split()

    # create / make
    if re.search(r'(?:^|\s)(create|make)\s+(?:a\s+)?(?:folder|directory)\s+', lower):
        return f"mkdir {toks[-1]}"

    # delete / remove
    if re.search(r'(?:^|\s)(delete|remove)\s+(?:the\s+)?(?:file|folder|directory)\s+', lower):
        name = toks[-1]
        if not os.path.splitext(name)[1]:  # no extension → folder
            return f"rm -r {name}"
        return f"rm {name}"

    # move
    if "move" in lower and (" to " in lower or " into " in lower):
        sep = " to " if " to " in lower else " into "
        parts = t.split(sep, 1)
        if len(parts) == 2:
            left, right = parts[0], parts[1]
            left = re.sub(r'^\s*move\s*(?:file|folder|directory)?\s*', '', left, flags=re.IGNORECASE)
            return f"mv {left.strip()} {right.strip()}"

    # copy
    if "copy" in lower and " to " in lower:
        parts = t.split(" to ", 1)
        if len(parts) == 2:
            left, right = parts[0], parts[1]
            left = re.sub(r'^\s*copy\s*(?:file|folder|directory)?\s*', '', left, flags=re.IGNORECASE)
            return f"cp {left.strip()} {right.strip()}"

    # read/open/show file
    if re.search(r'(?:^|\s)(read|open|show)\s+(?:file\s+)?', lower):
        return f"cat {toks[-1]}"

    return None
