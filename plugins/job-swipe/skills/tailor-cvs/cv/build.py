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
import importlib, os, pathlib, re, shutil, subprocess, sys, time, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent
VENV = pathlib.Path.home() / ".cache" / "job-swipe" / "venv"  # used only when the system Python refuses pip installs
APT_TIMEOUT = 540  # seconds for all installs together; stays under the 10-minute limit of one Bash tool call
_apt_deadline = None
_apt_timed_out = False  # a timed-out apt-get keeps running and holds the lock; later installs would just fail

jinja2 = yaml = None  # imported by ensure_python_deps() from main()


def _say(msg):
    print(msg, file=sys.stderr, flush=True)


def _apt(*pkgs):
    """Best-effort apt install (fresh cloud sessions). Returns False if apt is missing, failed or timed out."""
    global _apt_deadline, _apt_timed_out
    if not shutil.which("apt-get") or _apt_timed_out:
        return False
    if _apt_deadline is None:
        _apt_deadline = time.monotonic() + APT_TIMEOUT
    _say("Installing " + ", ".join(pkgs) + " (first run on this machine, this can take a few minutes)...")
    cmd = "apt-get install -y -q {0} || (apt-get update -q && apt-get install -y -q {0})".format(" ".join(pkgs))
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=max(1, _apt_deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        _apt_timed_out = True
        _say("The install timed out; it keeps going in the background.")
        return False
    if r.returncode:
        _say("The install failed:\n" + ((r.stderr or "") + (r.stdout or ""))[-1500:])
    return r.returncode == 0


def _import_deps():
    return importlib.import_module("jinja2"), importlib.import_module("yaml")


def _pip(python, *extra):
    return subprocess.run([python, "-m", "pip", "install", "-q", *extra, "jinja2", "pyyaml"],
                          capture_output=True, text=True)


def ensure_python_deps():
    """Return (jinja2, yaml), installing them if needed.

    Tries pip for this Python first; where that is refused (externally-managed Pythons, PEP 668) it installs
    into a private venv and re-runs this script with that venv's Python.
    """
    try:
        return _import_deps()
    except ImportError:
        pass
    errors = []
    if not os.environ.get("JOB_SWIPE_VENV"):
        r = _pip(sys.executable)
        if r.returncode == 0:
            importlib.invalidate_caches()
            try:
                return _import_deps()
            except ImportError:
                pass
        errors.append(r.stderr or r.stdout)
        py = VENV / "bin" / "python"
        if not py.exists():
            r = subprocess.run([sys.executable, "-m", "venv", str(VENV)], capture_output=True, text=True)
            errors.append(r.stderr or r.stdout)
        try:
            r = _pip(str(py))
        except OSError as e:  # the venv could not be created at all
            r = subprocess.CompletedProcess([], 1, "", str(e))
        if r.returncode != 0:
            shutil.rmtree(VENV, ignore_errors=True)  # e.g. built without pip; start clean next time
        else:
            os.environ["JOB_SWIPE_VENV"] = "1"
            os.execv(str(py), [str(py), str(pathlib.Path(__file__).resolve()), *sys.argv[1:]])
        errors.append(r.stderr or r.stdout)
    detail = "\n".join(e.strip() for e in errors if e and e.strip())[-1500:]
    sys.exit(f"Missing Python packages jinja2 and pyyaml, and installing them failed.\n{detail}\n"
             f"Install them for {sys.executable} (or in a virtual environment), then try again.")


def ensure_tools():
    """LaTeX renders, poppler counts pages and checks the text; fresh cloud sessions may lack either."""
    if not shutil.which("pdflatex"):
        # enumitem and titlesec live in texlive-latex-extra on Debian/Ubuntu.
        _apt("texlive-latex-base", "texlive-latex-recommended", "texlive-fonts-recommended", "texlive-latex-extra")
    if not (shutil.which("pdftotext") and shutil.which("pdfinfo")):
        _apt("poppler-utils")
    missing = [t for t in ("pdflatex", "pdftotext", "pdfinfo", "kpsewhich") if not shutil.which(t)]
    if missing and _apt_timed_out:
        sys.exit("Still installing LaTeX in the background: wait 5 minutes, then run the same command again.")
    if missing:
        sys.exit("Missing tools: " + ", ".join(missing) + ". Install a LaTeX distribution (e.g. TeX Live or MacTeX) "
                 "and poppler (pdftotext/pdfinfo), then try again.")
    # Latin Modern is needed for a clean T1 text layer + euro sign.
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
    global jinja2, yaml
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    jinja2, yaml = ensure_python_deps()
    ensure_tools()
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
