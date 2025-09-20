#!/usr/bin/env bash
set -e
echo "Running smoke tests for python-terminal-assignment"
python - <<'PY'
import subprocess, time, os
p = subprocess.Popen(['python','main.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
# we won't run interactive UI; instead test run_command via a tiny python import test
from commands import run_command
cwd = os.getcwd()
for cmd in ['pwd','ls','.','mkdir test_auto','ls','rm test_auto']:
    out, newcwd = run_command(cmd, cwd)
    print("CMD:",cmd)
    print(out)
print("Smoke tests done")
PY
echo "Done."
