#!/usr/bin/env python3
"""Build a tailored, one-page, ATS-safe CV from a person's master CV + a job spec.

usage: python3 build.py <master_cv.yaml> <job_spec.yaml> [out_dir]   (out_dir defaults to ./cv_out)

- master_cv.yaml: every true fact about the person (see examples/master_cv.example.yaml).
- job_spec.yaml:  which facts to show for one job, in which order, with which wording
                  (see examples/job_spec.example.yaml). Every field is optional.

All text is plain text: LaTeX special characters are escaped automatically.

Guarantees: fits the page limit (style.max_pages, default 1) (tightens spacing, then drops the lowest-priority
bullets / optional sections, and reports what it dropped), and a clean text layer
(checked with pdftotext the way an ATS parser reads it).
"""
import pathlib, re, shutil, subprocess, sys, unicodedata


def _apt(*pkgs):
    """Best-effort apt install (fresh cloud sessions); silently does nothing where apt is unavailable."""
    if shutil.which("apt-get"):
        cmd = "apt-get install -y -q {0} || (apt-get update -q && apt-get install -y -q {0})".format(" ".join(pkgs))
        subprocess.run(cmd, shell=True, capture_output=True)


try:
    import jinja2, yaml
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "jinja2", "pyyaml"], capture_output=True)
    try:
        import jinja2, yaml
    except ImportError:
        sys.exit("Missing Python packages: run `python3 -m pip install jinja2 pyyaml`, then try again.")

# Fresh cloud sessions may lack LaTeX or poppler; LaTeX is needed to render, poppler to count pages and check the text.
if not shutil.which("pdflatex"):
    _apt("texlive-latex-base", "texlive-latex-recommended", "texlive-fonts-recommended", "texlive-latex-extra")
if not (shutil.which("pdftotext") and shutil.which("pdfinfo")):
    _apt("poppler-utils")
_missing = [t for t in ("pdflatex", "pdftotext", "pdfinfo", "kpsewhich") if not shutil.which(t)]
if _missing:
    sys.exit("Missing tools: " + ", ".join(_missing) + ". Install a LaTeX distribution (e.g. TeX Live or MacTeX) "
             "and poppler (pdftotext/pdfinfo), then try again.")

ROOT = pathlib.Path(__file__).resolve().parent

# Fresh cloud sessions may lack Latin Modern (needed for a clean T1 text layer + euro sign).
if subprocess.run(["kpsewhich", "lmodern.sty"], capture_output=True, text=True).stdout.strip() == "":
    _apt("lmodern")

# Spacing presets, loosest first; the builder walks down until the CV fits on one page.
PRESETS = [
    dict(font="11pt", top="1.4cm", bottom="1.3cm", side="1.6cm", spread="1.06", itemsep="2pt", secbefore="10pt", secafter="5pt", rolegap="4pt"),
    dict(font="11pt", top="1.2cm", bottom="1.1cm", side="1.45cm", spread="1.02", itemsep="1pt", secbefore="7pt", secafter="4pt", rolegap="2pt"),
    dict(font="10pt", top="1.3cm", bottom="1.2cm", side="1.5cm", spread="1.04", itemsep="1.5pt", secbefore="8pt", secafter="5pt", rolegap="3pt"),
    dict(font="10pt", top="1.1cm", bottom="1.0cm", side="1.35cm", spread="1.0", itemsep="1pt", secbefore="6pt", secafter="4pt", rolegap="2pt"),
    dict(font="10pt", top="0.9cm", bottom="0.9cm", side="1.2cm", spread="0.98", itemsep="0.5pt", secbefore="5pt", secafter="3pt", rolegap="1pt"),
]

_TEX = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
        "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        "€": r"\euro{}", "–": "--", "—": "---", "’": "'", "‘": "`", "“": "``", "”": "''",
        "•": "", "…": "...", " ": "~", "→": r"$\rightarrow$", "×": r"$\times$", "≈": r"$\approx$",
        "<": r"\textless{}", ">": r"\textgreater{}", "|": r"\textbar{}"}


def tex(s):
    """Plain text -> LaTeX-safe text. Whitespace is collapsed."""
    if s is None:
        return ""
    s = " ".join(str(s).split())
    return "".join(_TEX.get(ch, ch) for ch in s)


def plain(s):
    return " ".join(str(s or "").split())


def load(p):
    return yaml.safe_load(pathlib.Path(p).read_text()) or {}


def jenv():
    return jinja2.Environment(
        block_start_string=r"\BLOCK{", block_end_string="}",
        variable_start_string=r"\VAR{", variable_end_string="}",
        comment_start_string=r"\#{", comment_end_string="}",
        trim_blocks=True, autoescape=False,
        loader=jinja2.FileSystemLoader(str(ROOT)))


FONTS = ("classic", "charter", "palatino", "sans")
BASE_SECTIONS = ["summary", "experience", "education", "skills"]


def get_style(master):
    st = dict(master.get("style") or {})
    font = st.get("font", "classic")
    accent = str(st.get("accent") or "1B6FB0").lstrip("#").upper()
    if not re.fullmatch(r"[0-9A-F]{6}", accent):
        accent = "1B6FB0"
    extra_ids = [s["id"] for s in master.get("extra_sections") or []]
    order = [x for x in (st.get("section_order") or []) if x in BASE_SECTIONS + extra_ids]
    order += [x for x in BASE_SECTIONS + extra_ids if x not in order]
    return dict(font=font if font in FONTS else "classic", accent=accent,
                heading_color="accent" if st.get("color_headings", False) else "black",
                name_case="as_written" if st.get("name_case") == "as_written" else "upper",
                sections=order, max_pages=2 if st.get("max_pages") == 2 else 1)


def track_cfg(master, spec):
    return (master.get("tracks") or {}).get(spec.get("track") or "", {}) or {}


def chosen_bullets(master, spec):
    """{role_id: [bullet ids in display order]} — spec, else track default, else everything."""
    order = spec.get("roles") or track_cfg(master, spec).get("roles")
    if order:
        return {k: list(v or []) for k, v in order.items()}
    return {r["id"]: [b["id"] for b in r.get("bullets", [])] for r in master.get("experience", [])}


def skill_rows(master, spec):
    rows = [(r["label"], list(r.get("items") or [])) for r in master.get("skills") or []]
    if master.get("certificates"):
        rows.append(("Certifications", list(master["certificates"])))
    if master.get("languages"):
        langs = master["languages"]
        rows.append(("Languages", langs if isinstance(langs, list) else [langs]))
    wanted = spec.get("skills_order") or track_cfg(master, spec).get("skills_order")
    if wanted:
        by = dict(rows)
        rows = [(l, by[l]) for l in wanted if l in by] + [(l, v) for l, v in rows if l not in wanted]
    front = spec.get("skills_front") or {}
    out = []
    for label, items in rows:
        f = [x for x in front.get(label, []) if x in items]  # only re-order, never add
        items = f + [x for x in items if x not in f]
        sep = "; " if label == "Certifications" else ", "
        out.append((tex(label), sep.join(tex(x) for x in items)))
    return out


def assemble(master, spec, drop):
    over = spec.get("overrides") or {}
    track = spec.get("track")
    order = chosen_bullets(master, spec)
    roles = []
    for r in master.get("experience", []):
        byid = {b["id"]: b for b in r.get("bullets", [])}
        bullets = []
        for bid in order.get(r["id"], []):
            if bid in drop or bid not in byid:
                continue
            b = byid[bid]
            text = over.get(bid) or (b.get("variants") or {}).get(track) or b["text"]
            bullets.append(tex(text))
        if r["id"] not in order:  # role left out of this CV on purpose
            continue
        # a role whose bullets were all trimmed still shows its title line (no gaps in the timeline)
        roles.append(dict(title=tex(r["title"]), company=tex(r.get("company")), location=tex(r.get("location")),
                          dates=tex(r.get("dates")), bullets=bullets,
                          stack=tex((spec.get("stack") or {}).get(r["id"]) or r.get("stack"))))
    edu = [dict(degree=tex(e["degree"]), school=tex(e.get("school")), dates=tex(e.get("dates")),
                detail=tex(e.get("detail"))) for e in master.get("education", [])
           if not ("edu:" + e.get("id", "")) in drop]
    extras = {}
    for s in master.get("extra_sections") or []:
        if ("sec:" + s["id"]) in drop or s["id"] in (spec.get("hide_sections") or []):
            continue
        extras[s["id"]] = dict(title=tex(s["title"]), bulleted=bool(s.get("bulleted")),
                               lines=[tex(i) for i in s.get("items", [])])
    h = master["header"]
    contact = []
    for c in h.get("contact") or []:
        c = plain(c)
        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", c):
            contact.append(r"\href{mailto:%s}{%s}" % (c, tex(c)))
        elif re.match(r"(https?://)?([\w-]+\.)+[a-z]{2,}(/\S*)?$", c, re.I) and " " not in c:
            url = c if c.startswith("http") else "https://" + c
            contact.append(r"\href{%s}{%s}" % (url.replace("%", r"\%").replace("#", r"\#"), tex(re.sub(r"^https?://", "", c))))
        else:
            contact.append(tex(c))
    headline = spec.get("headline") or track_cfg(master, spec).get("headline") or h.get("headline") or ""
    summary = spec.get("summary") or track_cfg(master, spec).get("summary") or master.get("summary")
    if "summary" in drop:
        summary = None
    style = get_style(master)
    return dict(style=style, sections=style["sections"], name=tex(h["name"]), headline=tex(headline), headline_plain=plain(headline),
                contact=contact, summary=tex(summary) if summary else None, roles=roles,
                education=edu, skill_rows=skill_rows(master, spec), extras=extras)


def compile_pdf(src, workdir, name):
    (workdir / f"{name}.tex").write_text(src)
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
                       cwd=workdir, capture_output=True, text=True)
    if r.returncode:
        sys.exit("LaTeX failed (check for unusual characters in the YAML):\n" + r.stdout[-3000:])
    info = subprocess.run(["pdfinfo", f"{name}.pdf"], cwd=workdir, capture_output=True, text=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", info).group(1))


def trim_candidates(master, spec):
    """Lowest value first: priority-3 bullets, optional sections, then priority-2 bullets."""
    pinned = set(spec.get("pinned") or [])
    order = chosen_bullets(master, spec)
    pri = {b["id"]: b.get("priority", 2) for r in master.get("experience", []) for b in r.get("bullets", [])}
    listed = [b for ids in order.values() for b in ids if b not in pinned and b in pri]
    c = sorted([b for b in listed if pri[b] >= 3], key=lambda b: -listed.index(b))
    c += ["sec:" + s["id"] for s in reversed(master.get("extra_sections") or []) if s.get("optional", True)]
    c += ["edu:" + e["id"] for e in reversed(master.get("education") or []) if e.get("optional")]
    c += ["summary"] if not spec.get("summary") else []
    c += sorted([b for b in listed if pri[b] == 2], key=lambda b: -listed.index(b))
    return c


def ats_check(pdf, master, spec):
    raw = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout
    problems = []
    bad = sorted({ch for ch in raw if unicodedata.category(ch) in ("Co", "Cn") or ch == "�"})
    if bad:
        problems.append(f"unmapped glyphs: {bad}")
    first = raw.strip().splitlines()[0].strip() if raw.strip() else ""
    if first.upper() != plain(master["header"]["name"]).upper():
        problems.append(f"first line is not the name: {first!r}")
    lines = [l.strip().upper() for l in raw.splitlines()]
    want = [s.upper() for s in get_style(master)["sections"] if s in ("experience", "education", "skills")]
    pos = [next((i for i, l in enumerate(lines) if l == s), -1) for s in want]
    if -1 in pos or pos != sorted(pos):
        problems.append(f"section order/labels off: {pos}")
    src = pathlib.Path(str(pdf)[:-4] + ".tex").read_text()
    if "\\euro" in src.split("\\begin{document}", 1)[-1] and "€" not in raw:
        problems.append("euro sign not extractable")
    for c in master["header"].get("contact") or []:
        if "@" in str(c) and plain(c) not in raw:
            problems.append("email not extractable")
    low = " ".join(raw.lower().split())
    kws = spec.get("keywords") or []
    hit = [k for k in kws if k.lower() in low]
    miss = [k for k in kws if k.lower() not in low]
    return raw, problems, hit, miss


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    master = load(sys.argv[1])
    spec_path = pathlib.Path(sys.argv[2])
    spec = load(spec_path)
    person = re.sub(r"[^A-Za-z0-9]+", "_", unicodedata.normalize("NFKD", master["header"]["name"]).encode("ascii", "ignore").decode()).strip("_")
    company = re.sub(r"[^A-Za-z0-9]+", "_", unicodedata.normalize("NFKD", str(spec.get("company") or spec_path.stem)).encode("ascii", "ignore").decode()).strip("_")
    name = f"{person}_CV_{company}"
    out = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else "cv_out").resolve() / spec_path.stem
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    tpl = jenv().get_template("template.tex.j2")

    max_pages = get_style(master)["max_pages"]
    dropped, cands = [], trim_candidates(master, spec)
    while True:
        for i, m in enumerate(PRESETS):
            ctx = assemble(master, spec, set(dropped))
            ctx["m"] = m
            pages = compile_pdf(tpl.render(**ctx), out, name)
            if pages <= max_pages:
                break
        else:
            if not cands:
                sys.exit(f"Cannot fit on {max_pages} page(s) even after trimming: list fewer bullets in the job spec.")
            dropped.append(cands.pop(0))
            continue
        break

    raw, problems, hit, miss = ats_check(out / f"{name}.pdf", master, spec)
    (out / f"{name}.txt").write_text(raw)
    for f in out.glob(f"{name}.*"):
        if f.suffix in (".aux", ".log", ".out"):
            f.unlink()
    report = [f"PDF: {out / (name + '.pdf')}", f"Pages: {pages} (limit {max_pages})",
              f"Spacing preset: {i + 1}/{len(PRESETS)}",
              f"Dropped to fit: {dropped or 'nothing'}",
              f"ATS text check: {'OK' if not problems else problems}"]
    if kws := spec.get("keywords"):
        report.append(f"Keywords present ({len(hit)}/{len(kws)}): {hit}")
        report.append(f"Keywords missing: {miss}")
    print("\n".join(report))
    (out / "report.txt").write_text("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
