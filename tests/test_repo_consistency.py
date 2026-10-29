"""Repo-wide facts a release depends on: manifests parse, the version agrees everywhere, pinned files still match."""
import base64, hashlib, json, os, pathlib, re, subprocess, unittest, urllib.request

REPO = pathlib.Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins/job-swipe"
BOARD = PLUGIN / "board/job-swipe.html"
NETWORK = os.environ.get("NETWORK") == "1" or os.environ.get("CI") == "true"
VERSION_BASE = os.environ.get("VERSION_BASE")  # git ref to compare against, e.g. origin/main (set by CI)


def plugin_version():
    return json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())["version"]


class ManifestTest(unittest.TestCase):
    def test_manifests_are_valid_json(self):
        for p in (REPO / ".claude-plugin/marketplace.json", PLUGIN / ".claude-plugin/plugin.json"):
            with self.subTest(p.name):
                json.loads(p.read_text())

    def test_marketplace_points_at_the_plugin(self):
        market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
        entry = next(x for x in market["plugins"] if x["name"] == "job-swipe")
        self.assertEqual((REPO / entry["source"]).resolve(), PLUGIN)

    def test_license_is_declared_and_present(self):
        self.assertEqual(json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text()).get("license"), "MIT")
        self.assertTrue((REPO / "LICENSE").read_text().startswith("MIT License"))


class VersionTest(unittest.TestCase):
    def test_changelog_top_entry_is_the_plugin_version(self):
        top = re.search(r"^## (\S+)", (REPO / "CHANGELOG.md").read_text(), re.M).group(1)
        self.assertEqual(top, plugin_version())

    def test_board_version_is_the_plugin_version(self):
        board = re.search(r'const BOARD_VERSION = "([^"]+)"', BOARD.read_text(encoding="utf-8")).group(1)
        self.assertEqual(board, plugin_version())

    @unittest.skipUnless(VERSION_BASE, "set VERSION_BASE=<git ref> to compare with (CI does)")
    def test_plugin_changes_bump_the_version(self):
        git = lambda *a: subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True, check=True).stdout
        changed = git("diff", "--name-only", f"{VERSION_BASE}...HEAD", "--", "plugins/").split()
        if not changed:
            return
        before = json.loads(git("show", f"{VERSION_BASE}:plugins/job-swipe/.claude-plugin/plugin.json"))["version"]
        self.assertNotEqual(before, plugin_version(),
                            f"{len(changed)} file(s) under plugins/ changed but plugin.json is still {before}: "
                            "bump the version so installs pick the change up")


class PdfjsPinTest(unittest.TestCase):
    def pins(self):
        html = BOARD.read_text(encoding="utf-8")
        return re.findall(r'url:\s*"(https://cdnjs[^"]+)",\s*sha384:\s*"(sha384-[^"]+)"', html)

    def test_both_files_are_pinned_to_one_version(self):
        pins = self.pins()
        self.assertEqual(len(pins), 2)
        version = re.search(r'version:\s*"([^"]+)"', BOARD.read_text(encoding="utf-8")).group(1)
        for url, _ in pins:
            self.assertIn("/" + version + "/", url)

    @unittest.skipUnless(NETWORK, "downloads from cdnjs: set NETWORK=1 (CI does)")
    def test_cdnjs_files_still_match_the_pinned_hashes(self):
        for url, want in self.pins():
            with self.subTest(url), urllib.request.urlopen(url, timeout=60) as r:
                got = "sha384-" + base64.b64encode(hashlib.sha384(r.read()).digest()).decode()
                self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()
