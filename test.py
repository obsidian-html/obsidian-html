import re

with open('test.txt') as f:
    data  = f.read()

matches = re.findall("(?<![\[\(])(http.[^\s]*)", data)

for match in matches:
    new = f"[{match}]({match})"
    safe_match = re.escape(match)
    data = re.sub(f"(?<![\[\(])({safe_match})", new, data)

print(data)