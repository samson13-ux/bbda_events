"""Injecte {% include '_csrf.html' %} dans tous les formulaires POST."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "templates"
MARKER = "{% include '_csrf.html' %}"


def main():
    count = 0
    for path in ROOT.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if "method=\"post\"" not in text.lower() and "method='post'" not in text.lower():
            continue
        if MARKER in text or "csrf_token()" in text:
            print("skip", path.relative_to(ROOT))
            continue

        lines = text.splitlines(keepends=True)
        out = []
        i = 0
        changed = False
        while i < len(lines):
            line = lines[i]
            out.append(line)
            low = line.lower().replace("'", '"')
            if "<form" in low and 'method="post"' in low:
                buf = line
                j = i
                while ">" not in buf and j + 1 < len(lines):
                    j += 1
                    buf += lines[j]
                    out.append(lines[j])
                i = j
                indent = "    "
                for k in range(i + 1, min(i + 6, len(lines))):
                    if lines[k].strip():
                        indent = lines[k][: len(lines[k]) - len(lines[k].lstrip())]
                        break
                out.append(f"{indent}{MARKER}\n")
                changed = True
            i += 1

        if changed:
            path.write_text("".join(out), encoding="utf-8")
            count += 1
            print("patched", path.relative_to(ROOT))
    print("total", count)


if __name__ == "__main__":
    main()
