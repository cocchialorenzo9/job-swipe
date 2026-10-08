"""Dependency bootstrap of the CV builder: it must never hang a run or hide why an install failed."""
import importlib.util, pathlib, subprocess, sys, unittest
from unittest import mock

BUILD = pathlib.Path(__file__).resolve().parents[1] / "plugins/job-swipe/skills/tailor-cvs/cv/build.py"


def load_build():
    spec = importlib.util.spec_from_file_location("cv_build", BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # importing must not install or exit
    return mod


def done(code=0, out="", err=""):
    return subprocess.CompletedProcess([], code, out, err)


class AptTest(unittest.TestCase):
    def setUp(self):
        self.b = load_build()

    def test_install_has_a_timeout_below_the_bash_tool_limit(self):
        with mock.patch.object(self.b.shutil, "which", return_value="/usr/bin/apt-get"), \
             mock.patch.object(self.b.subprocess, "run", return_value=done()) as run:
            self.b._apt("poppler-utils")
        self.assertLess(run.call_args.kwargs["timeout"], 600)

    def test_timeout_is_reported_not_raised(self):
        err = subprocess.TimeoutExpired("apt-get", 1)
        with mock.patch.object(self.b.shutil, "which", return_value="/usr/bin/apt-get"), \
             mock.patch.object(self.b.subprocess, "run", side_effect=err), \
             mock.patch("sys.stderr") as stderr:
            self.b._apt("texlive-latex-base")
        self.assertIn("timed out", "".join(c.args[0] for c in stderr.write.call_args_list))

    def test_installs_share_one_time_budget(self):
        clock = iter([1000.0, 1000.0, 1500.0])  # first install took 500s of the budget
        with mock.patch.object(self.b.shutil, "which", return_value="/usr/bin/apt-get"), \
             mock.patch.object(self.b.time, "monotonic", side_effect=lambda: next(clock)), \
             mock.patch.object(self.b.subprocess, "run", return_value=done()) as run:
            self.b._apt("texlive-latex-base")
            self.b._apt("poppler-utils")
        self.assertLessEqual(run.call_args.kwargs["timeout"], self.b.APT_TIMEOUT - 500)

    def test_timed_out_install_stops_later_installs(self):
        err = subprocess.TimeoutExpired("apt-get", 1)
        with mock.patch.object(self.b.shutil, "which", return_value="/usr/bin/apt-get"), \
             mock.patch.object(self.b.subprocess, "run", side_effect=err) as run, \
             mock.patch("sys.stderr"):
            self.assertFalse(self.b._apt("texlive-latex-base"))
            self.assertFalse(self.b._apt("poppler-utils"))  # apt still holds the lock: don't queue behind it
        self.assertEqual(run.call_count, 1)

    def test_no_apt_does_nothing(self):
        with mock.patch.object(self.b.shutil, "which", return_value=None), \
             mock.patch.object(self.b.subprocess, "run") as run:
            self.b._apt("lmodern")
        run.assert_not_called()


class PythonDepsTest(unittest.TestCase):
    def setUp(self):
        self.b = load_build()

    def test_already_installed(self):
        with mock.patch.object(self.b, "_import_deps", return_value=("j", "y")), \
             mock.patch.object(self.b.subprocess, "run") as run:
            self.assertEqual(self.b.ensure_python_deps(), ("j", "y"))
        run.assert_not_called()

    def test_externally_managed_python_falls_back_to_private_venv_and_reruns(self):
        pep668 = done(1, err="error: externally-managed-environment")
        with mock.patch.object(self.b, "_import_deps", side_effect=ImportError), \
             mock.patch.object(self.b.subprocess, "run", side_effect=[pep668, done(), done()]) as run, \
             mock.patch.object(self.b.os, "execv", side_effect=SystemExit) as execv, \
             mock.patch.dict(self.b.os.environ, {}, clear=False), \
             mock.patch.object(self.b.pathlib.Path, "exists", return_value=False), \
             self.assertRaises(SystemExit):  # a real execv never returns
            self.b.ensure_python_deps()
        venv_py = str(self.b.VENV / "bin" / "python")
        self.assertEqual(run.call_args_list[1].args[0][1:3], ["-m", "venv"])
        self.assertEqual(run.call_args_list[2].args[0][0], venv_py)
        self.assertEqual(execv.call_args.args[0], venv_py)
        self.assertEqual(execv.call_args.args[1][1], str(BUILD))

    def test_failure_shows_pip_error(self):
        pep668 = done(1, err="error: externally-managed-environment")
        with mock.patch.object(self.b, "_import_deps", side_effect=ImportError), \
             mock.patch.object(self.b.subprocess, "run", side_effect=[pep668, done(1, err="no venv module"), done(1)]), \
             mock.patch.object(self.b.shutil, "rmtree") as rmtree, \
             mock.patch.object(self.b.os, "execv") as execv, \
             mock.patch.object(self.b.pathlib.Path, "exists", return_value=False), \
             self.assertRaises(SystemExit) as exit_:
            self.b.ensure_python_deps()
        execv.assert_not_called()
        rmtree.assert_called_once_with(self.b.VENV, ignore_errors=True)  # a half-built venv must not stick
        self.assertIn("externally-managed-environment", str(exit_.exception))
        self.assertIn(sys.executable, str(exit_.exception))

    def test_missing_venv_python_is_reported_not_raised(self):
        pep668 = done(1, err="error: externally-managed-environment")
        with mock.patch.object(self.b, "_import_deps", side_effect=ImportError), \
             mock.patch.object(self.b.subprocess, "run",
                               side_effect=[pep668, done(1, err="no venv module"), FileNotFoundError("python")]), \
             mock.patch.object(self.b.shutil, "rmtree"), \
             mock.patch.object(self.b.pathlib.Path, "exists", return_value=False), \
             self.assertRaises(SystemExit) as exit_:
            self.b.ensure_python_deps()
        self.assertIn("no venv module", str(exit_.exception))

    def test_does_not_loop_when_already_rerun_in_the_venv(self):
        with mock.patch.object(self.b, "_import_deps", side_effect=ImportError), \
             mock.patch.object(self.b.subprocess, "run", return_value=done(1, err="boom")), \
             mock.patch.object(self.b.os, "execv") as execv, \
             mock.patch.dict(self.b.os.environ, {"JOB_SWIPE_VENV": "1"}), \
             self.assertRaises(SystemExit):
            self.b.ensure_python_deps()
        execv.assert_not_called()


if __name__ == "__main__":
    unittest.main()
