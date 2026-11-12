"""Запускать только внутри одноразового Docker-контейнера от root.

Проверяется весь install.sh с настоящими файлами; Poetry и systemctl заменены
заглушками, чтобы не скачивать зависимости и не запускать службы.
"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from uuid import uuid4


REPO = Path(__file__).resolve().parents[2]


class InstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path("/.dockerenv").exists() or os.getuid() != 0:
            raise RuntimeError("Тест изменяет /etc/systemd: запускайте в одноразовом Docker-контейнере от root")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="osips-install-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "repo"
        for directory in ("install", "back-osips-ui", "front-osips-ui/dist"):
            (self.repo / directory).mkdir(parents=True)
        for filename in ("install.sh", "osips-ui.service.template"):
            shutil.copyfile(REPO / "install" / filename, self.repo / "install" / filename)
        shutil.copyfile(REPO / "back-osips-ui/.env.example", self.repo / "back-osips-ui/.env.example")
        (self.repo / "front-osips-ui/dist/index.html").write_text("<html>test</html>")
        self.target = self.base / "installed"
        self.service = "osips-test-" + uuid4().hex
        self.unit = Path("/etc/systemd/system") / f"{self.service}.service"
        self.unit.parent.mkdir(parents=True, exist_ok=True)
        self.addCleanup(self.unit.unlink, missing_ok=True)
        self.calls = self.base / "systemctl.calls"
        binaries = self.base / "bin"
        binaries.mkdir()
        for name, script in {
            "poetry": '#!/bin/sh\nif [ "$1" = "--version" ]; then echo "Poetry (version 2.3.2)"; fi\n',
            "systemctl": '#!/bin/sh\nprintf "%s\\n" "$*" >> "$SYSTEMCTL_CALLS"\n',
        }.items():
            executable = binaries / name
            executable.write_text(script)
            executable.chmod(0o755)
        self.env = os.environ | {
            "PATH": f"{binaries}:{os.environ['PATH']}",
            "POETRY_HOME": str(self.base / "poetry"),
            "SYSTEMCTL_CALLS": str(self.calls),
        }

    def install(self, *args):
        result = subprocess.run(
            ["bash", str(self.repo / "install/install.sh"), "--install-dir", str(self.target),
             "--user", "root", "--service-name", self.service, "--skip-frontend", *args],
            env=self.env, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.target / "back-osips-ui/.env").is_file())
        self.assertTrue((self.target / "front-osips-ui/dist/index.html").is_file())

    def test_no_service_does_not_create_unit(self):
        self.install("--no-service")
        self.assertFalse(self.unit.exists())
        self.assertFalse(self.calls.exists())

    def test_no_service_preserves_existing_unit(self):
        original = "# custom unit must survive\n[Service]\nExecStart=/custom/application\n"
        self.unit.write_text(original)
        self.unit.chmod(0o640)
        self.install("--no-service")
        self.assertEqual(self.unit.read_text(), original)
        self.assertEqual(self.unit.stat().st_mode & 0o777, 0o640)
        self.assertFalse(self.calls.exists())

    def test_no_service_migration_does_not_stop_service(self):
        previous = self.base / "previous/back-osips-ui"
        (previous / "data").mkdir(parents=True)
        (previous / ".env").write_text(f"APP_DB_PATH={previous}/data/osips-ui.db\n")
        (previous / "data/osips-ui.db").write_bytes(b"existing database")
        original = f"[Service]\nWorkingDirectory={previous}\n"
        self.unit.write_text(original)
        self.install("--no-service")
        self.assertEqual(self.unit.read_text(), original)
        self.assertFalse(self.calls.exists())
        self.assertEqual((self.target / "back-osips-ui/data/osips-ui.db").read_bytes(), b"existing database")

    def test_default_install_writes_unit_and_restarts_service(self):
        self.install()
        self.assertIn(f"WorkingDirectory={self.target}/back-osips-ui", self.unit.read_text())
        self.assertEqual(self.calls.read_text().splitlines(), ["daemon-reload", f"enable {self.service}", f"restart {self.service}"])


if __name__ == "__main__":
    unittest.main()
