"""Text from job postings and from the person ends up in LaTeX: odd characters must never break a CV build."""
import os, pathlib, shutil, subprocess, sys, tempfile, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_build_bootstrap import BUILD, load_build

EXAMPLES = BUILD.parent / "examples"
HAVE_LATEX = all(shutil.which(t) for t in ("pdflatex", "pdfinfo", "pdftotext", "kpsewhich"))
REQUIRE_LATEX = os.environ.get("REQUIRE_LATEX") == "1"  # CI: a skipped LaTeX test is a failure


class ClassifyContactTest(unittest.TestCase):
    def setUp(self):
        self.b = load_build()

    def test_plain_email_is_a_mailto_link(self):
        self.assertEqual(self.b.classify_contact("alex.example@example.com"),
                         ("email", "mailto:alex.example@example.com"))

    def test_web_address_without_scheme_gets_https(self):
        self.assertEqual(self.b.classify_contact("linkedin.com/in/alex-example"),
                         ("url", "https://linkedin.com/in/alex-example"))

    def test_underscores_and_tildes_stay_links(self):
        for c in ("linkedin.com/in/first_last", "github.com/foo_bar", "site.edu/~me"):
            self.assertEqual(self.b.classify_contact(c)[0], "url", c)

    def test_web_address_with_scheme_is_kept(self):
        self.assertEqual(self.b.classify_contact("http://alex.example.org/cv"), ("url", "http://alex.example.org/cv"))

    def test_phone_and_city_are_text(self):
        for c in ("+49 151 0000000", "Berlin, Germany"):
            self.assertEqual(self.b.classify_contact(c), ("text", None), c)

    def test_brace_breakout_is_text(self):
        payload = r"x}\input{/etc/hosts}\href{mailto:y@example.com"
        self.assertEqual(self.b.classify_contact(payload), ("text", None))

    def test_url_with_latex_characters_is_text(self):
        for c in (r"example.com/\input", "example.com/{x}", "example.com/a^b", "example.com/$x", "example .com"):
            self.assertEqual(self.b.classify_contact(c)[0], "text", c)


class ContactRenderTest(unittest.TestCase):
    def setUp(self):
        self.b = load_build()

    def render(self, c):
        return self.b.contact_items({"contact": [c]})

    def test_mailto_target_escapes_percent(self):
        items, unlinked = self.render("a%b@example.com")
        self.assertEqual(items, [r"\href{mailto:a\%b@example.com}{a\%b@example.com}"])
        self.assertEqual(unlinked, [])

    def test_url_target_escapes_percent_and_hash(self):
        items, _ = self.render("example.com/a%20b#top")
        self.assertEqual(items, [r"\href{https://example.com/a\%20b\#top}{example.com/a\%20b\#top}"])

    def test_breakout_is_escaped_plain_text_and_reported(self):
        payload = r"x}\input{/etc/hosts}\href{mailto:y@example.com"
        items, unlinked = self.render(payload)
        self.assertEqual(items, [self.b.tex(payload)])
        self.assertNotIn(r"\input{", items[0])
        self.assertEqual(unlinked, [payload])

    def test_address_like_text_is_reported(self):
        items, unlinked = self.render("example.com/a^b")
        self.assertEqual(items, [self.b.tex("example.com/a^b")])
        self.assertEqual(unlinked, ["example.com/a^b"])
        self.assertEqual(self.render("St. Pauli, Hamburg")[1], [])

    def test_phone_is_not_reported(self):
        self.assertEqual(self.render("+49 151 0000000"), ([self.b.tex("+49 151 0000000")], []))


class PdfStrTest(unittest.TestCase):
    def setUp(self):
        self.b = load_build()

    def test_escapes_only_hyperref_specials(self):
        self.assertEqual(self.b.pdfstr("Growth PM | 100% remote"), r"Growth PM | 100\% remote")
        self.assertEqual(self.b.pdfstr("Team #1 {x} R&D a_b $5 ~ ^"),
                         r"Team \#1 \{x\} R\&D a\_b \$5 \textasciitilde{} \textasciicircum{}")
        self.assertEqual(self.b.pdfstr("C:\\x"), r"C:\textbackslash{}x")

    def test_collapses_whitespace_and_none(self):
        self.assertEqual(self.b.pdfstr("  a \n b "), "a b")
        self.assertEqual(self.b.pdfstr(None), "")

    def test_template_uses_metadata_escaping(self):
        ctx = self.b.assemble({"header": {"name": "Alex Example"}}, {"headline": "100% remote"}, set())
        self.assertEqual(ctx["meta_headline"], r"100\% remote")
        self.assertNotIn("headline_plain", ctx)
        tpl = (BUILD.parent / "template.tex.j2").read_text()
        self.assertIn(r"pdfsubject={\VAR{meta_headline}}", tpl)
        self.assertNotIn("headline_plain", tpl)


class PipPinTest(unittest.TestCase):
    def test_pip_installs_pinned_major_versions(self):
        b = load_build()
        from unittest import mock
        with mock.patch.object(b.subprocess, "run") as run:
            b._pip("python3")
        args = run.call_args.args[0]
        self.assertIn("jinja2>=3,<4", args)
        self.assertIn("pyyaml>=6,<7", args)


@unittest.skipUnless(HAVE_LATEX or REQUIRE_LATEX, "needs pdflatex, kpsewhich, pdfinfo, pdftotext (CI sets REQUIRE_LATEX=1)")
class LatexBuildTest(unittest.TestCase):
    """Real builds of the example CV with hostile or unusual text."""

    @classmethod
    def setUpClass(cls):
        if not HAVE_LATEX:
            raise AssertionError("REQUIRE_LATEX=1 but LaTeX/poppler tools are missing")
        b = load_build()
        b.jinja2, b.yaml = b._import_deps()
        cls.b = b

    def build(self, headline=None, contact=None, name=None):
        yaml = self.b.yaml
        master = yaml.safe_load((EXAMPLES / "master_cv.example.yaml").read_text())
        spec = yaml.safe_load((EXAMPLES / "job_spec.example.yaml").read_text())
        if headline is not None:
            spec["headline"] = headline
        if contact is not None:
            master["header"]["contact"] = contact
        if name is not None:
            master["header"]["name"] = name
        tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "master.yaml").write_text(yaml.safe_dump(master, allow_unicode=True), encoding="utf-8")
        (tmp / "job.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
        r = subprocess.run([sys.executable, str(BUILD), str(tmp / "master.yaml"), str(tmp / "job.yaml"), str(tmp / "out")],
                           capture_output=True, text=True, cwd=tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        pdf = next((tmp / "out" / "job").glob("*.pdf"))
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        tex_src = pdf.with_suffix(".tex").read_text()
        return r.stdout, info, tex_src

    def subject(self, info):
        return next(l.split(":", 1)[1].strip() for l in info.splitlines() if l.startswith("Subject:"))

    def test_headlines_with_percent_hash_and_braces_build(self):
        for h in ("Growth PM | 100% remote", "Team #1 engineer", "{x}", "R&D Lead", "C++ engineer {embedded}"):
            with self.subTest(headline=h):
                report, info, _ = self.build(headline=h)
                self.assertIn("Pages: 1", report)
                self.assertIn("ATS text check: OK", report)
                self.assertEqual(self.subject(info), h)

    def test_non_ascii_name_and_headline_reach_the_metadata(self):
        h = "Ingénieur logiciel – Zürich → €80k"
        report, info, _ = self.build(headline=h, name="Jürgen Müller")
        self.assertIn("ATS text check: OK", report)
        self.assertEqual(self.subject(info), h)
        self.assertIn("Author:          Jürgen Müller", info)

    def test_breakout_contact_builds_as_plain_text(self):
        payload = r"x}\input{/etc/hosts}\href{mailto:y@example.com"
        report, _, tex_src = self.build(contact=["alex.example@example.com", payload])
        self.assertNotIn(payload, tex_src)
        self.assertIn("Contact shown without link: " + payload, report)

    def test_mailto_with_percent_builds(self):
        report, _, tex_src = self.build(contact=["a%b@example.com", "linkedin.com/in/alex-example"])
        self.assertIn(r"\href{mailto:a\%b@example.com}", tex_src)
        self.assertIn("ATS text check: OK", report)


if __name__ == "__main__":
    unittest.main()
