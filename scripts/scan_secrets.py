from pathlib import Path
import re
import sys
PATTERNS=[re.compile(r"sb_secret_[A-Za-z0-9_-]{12,}"),re.compile(r"sk-[A-Za-z0-9]{20,}"),re.compile(r"hf_[A-Za-z0-9]{20,}")]
violations=[]
for path in Path(".").rglob("*"):
    if not path.is_file() or ".git" in path.parts or path.stat().st_size>2_000_000: continue
    try:text=path.read_text()
    except UnicodeDecodeError:continue
    if any(pattern.search(text) for pattern in PATTERNS):violations.append(str(path))
if violations:print("possible secrets:\n"+"\n".join(violations));sys.exit(1)
print("secret scan: ok")
