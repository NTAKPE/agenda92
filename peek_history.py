# -*- coding: utf-8 -*-
"""Extrait les messages de l'utilisateur depuis les snapshots JSONL de session."""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def texts_of(content):
    if isinstance(content, str):
        return [content]
    out = []
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict):
                if c.get("type") in ("text", "input_text") and c.get("text"):
                    out.append(c["text"])
            elif isinstance(c, str):
                out.append(c)
    return out


for path in sys.argv[1:]:
    print()
    print("#" * 70)
    print("# %s" % os.path.basename(path))
    print("#" * 70)
    n = 0
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            role = obj.get("role") or obj.get("type") or ""
            msg = obj.get("message")
            if isinstance(msg, dict):
                role = msg.get("role") or role
                content = msg.get("content")
            else:
                content = obj.get("content") or obj.get("text")
            if str(role).lower() not in ("user", "human"):
                continue
            for t in texts_of(content):
                t = t.strip()
                if not t or t.startswith("<system-reminder") or "system-reminder" in t[:120]:
                    continue
                n += 1
                print()
                print("--- message utilisateur %d (ligne %d) ---" % (n, lineno))
                print(" ".join(t.split())[:700])
    print()
    print("=> %d message(s) utilisateur" % n)
