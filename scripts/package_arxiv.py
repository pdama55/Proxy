"""Builds the arXiv source bundle from the preprint driver.

    python scripts/package_arxiv.py [--out release]

Writes release/proxy-arxiv-src.tar.gz: paper/arxiv.tex as main.tex, every section, the generated numbers and
tables, only the figures the sections include, the bibliography, the two TMLR style files, and a 00README.json
that tells arXiv to compile with XeLaTeX (the drivers load fonts through fontspec). Also writes
release/arxiv-abstract.txt, the abstract with every macro expanded, for the submission form. Run
`python paper/build.py` first so numbers.tex, the tables and the figures are current.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "paper"


def expand_abstract() -> str:
    macros = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", (P / "numbers.tex").read_text()))
    a = (P / "sections" / "abstract.tex").read_text()
    a = re.sub(r"\\begin\{abstract\}|\\end\{abstract\}", "", a)
    a = re.sub(r"\\(\w+)(\\ |(?=[^\w]))", lambda m: macros.get(m.group(1), m.group(0)) + (" " if m.group(2) == "\\ " else ""), a)
    a = a.replace("\\%", "%").replace("--", "\u2013")
    return re.sub(r"\s+", " ", a).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "release"))
    args = ap.parse_args()
    out = Path(args.out)
    src = out / "arxiv-src"
    if src.exists():
        shutil.rmtree(src)
    for d in ("sections", "tables", "figures"):
        (src / d).mkdir(parents=True)
    shutil.copy(P / "arxiv.tex", src / "main.tex")
    for f in ("numbers.tex", "references.bib", "tmlr.sty", "tmlr.bst"):
        shutil.copy(P / f, src / f)
    for f in (P / "sections").glob("*.tex"):
        shutil.copy(f, src / "sections" / f.name)
    for f in (P / "tables").glob("*.tex"):
        shutil.copy(f, src / "tables" / f.name)
    sections = " ".join(f.read_text() for f in (P / "sections").glob("*.tex"))
    used = sorted(set(re.findall(r"includegraphics(?:\[[^]]*\])?\{figures/([^}]+)\}", sections)))
    for f in used:
        shutil.copy(P / "figures" / f, src / "figures" / f)
    readme = {"spec_version": 1, "process": {"compiler": "xelatex"}, "sources": [{"filename": "main.tex", "usage": "toplevel"}]}
    (src / "00README.json").write_text(json.dumps(readme, indent=1) + "\n")

    tar_path = out / "proxy-arxiv-src.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                tar.add(f, arcname=str(f.relative_to(src)))
    (out / "arxiv-abstract.txt").write_text(expand_abstract() + "\n")

    # Compile the bundle in isolation, exactly as uploaded, and report the page count.
    res = subprocess.run(["tectonic", "-X", "compile", "main.tex"], cwd=src, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit("bundle does not compile:\n" + res.stderr[-2000:])
    try:
        from pypdf import PdfReader

        pages = len(PdfReader(src / "main.pdf").pages)
    except ImportError:
        pages = "?"
    (src / "main.pdf").unlink(missing_ok=True)
    n = sum(1 for f in src.rglob("*") if f.is_file())
    print(f"{tar_path}  {tar_path.stat().st_size / 1e3:.0f} KB  {n} files  figures {used}  compiles to {pages} pages")


if __name__ == "__main__":
    main()
