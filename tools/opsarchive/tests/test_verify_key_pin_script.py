"""CI 검증 스크립트(`.github/scripts/verify_key_pin.py`)를 실제로 실행해 규칙을 고정한다.

이 스크립트는 CI 전용 사본이라 `opsarchive.pins.compare` 와 규칙이 갈라질 수 있다.
그래서 여기서 **실제 프로세스로** 돌려 armed/불일치/세대 판정을 확인한다.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

from opsarchive import commands, container as C, pins

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCRIPT = os.path.join(ROOT, ".github", "scripts", "verify_key_pin.py")
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "verify-key-pin.yml")


class VerifyScriptTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="opsarchive-ci-pin-")

    def _run(self, pin: dict, health: dict | None) -> subprocess.CompletedProcess:
        pin_path = os.path.join(self.dir, "pin.json")
        with open(pin_path, "w", encoding="utf-8") as fh:
            json.dump(pin, fh)
        argv = [sys.executable, SCRIPT, pin_path]
        if health is not None:
            health_path = os.path.join(self.dir, "health.json")
            with open(health_path, "w", encoding="utf-8") as fh:
                json.dump(health, fh)
            argv += ["--health-file", health_path]
        return subprocess.run(argv, capture_output=True, text=True,  # noqa: S603
                              encoding="utf-8", errors="replace")

    def test_unarmed_passes_with_warning(self):
        done = self._run({"schema": 1, "armed": False}, {"evidence": {}})
        self.assertEqual(done.returncode, 0)
        self.assertIn("미활성", done.stdout)

    def test_matching_pin_passes(self):
        shared = {"fingerprint": "ab" * 32, "key_id": "abcd1234", "generation": 2}
        done = self._run({"schema": 1, "armed": True, "fingerprint_sha256": "ab" * 32,
                          "generation": 2, "health_url": "https://example.test"},
                         {"evidence": shared})
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_mismatch_fails(self):
        done = self._run({"schema": 1, "armed": True, "fingerprint_sha256": "ab" * 32,
                          "generation": 2, "health_url": "https://example.test"},
                         {"evidence": {"fingerprint": "cd" * 32, "generation": 2}})
        self.assertEqual(done.returncode, 1)
        self.assertIn("fingerprint_mismatch", done.stdout)

    def test_missing_evidence_fails(self):
        done = self._run({"schema": 1, "armed": True, "fingerprint_sha256": "ab" * 32,
                          "generation": 1, "health_url": "https://example.test"}, {"ok": True})
        self.assertEqual(done.returncode, 1)
        self.assertIn("health_missing_evidence", done.stdout)

    def test_generation_regression_fails(self):
        done = self._run({"schema": 1, "armed": True, "fingerprint_sha256": "ab" * 32,
                          "generation": 3, "health_url": "https://example.test"},
                         {"evidence": {"fingerprint": "ab" * 32, "generation": 2}})
        self.assertEqual(done.returncode, 1)
        self.assertIn("generation_lower", done.stdout)


class VerifyScriptCiTest(unittest.TestCase):
    """CI 경로(`--expected-*`) 판정을 실제 프로세스로 고정한다.

    PowerShell 은 빈 문자열 인자를 드롭하므로, 빈 값 케이스는 subprocess 로 argv 를 직접 구성한다.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="opsarchive-ci-pin-ci-")

    def _run_ci(self, *, fingerprint: str, generation: str, key_id: str | None = None,
                health: dict | None = None, health_url: str = "https://example.test"):
        argv = [sys.executable, SCRIPT,
                "--expected-fingerprint", fingerprint,
                "--expected-generation", generation,
                "--health-url", health_url]
        if key_id is not None:
            argv += ["--expected-key-id", key_id]
        if health is not None:
            health_path = os.path.join(self.dir, "health.json")
            with open(health_path, "w", encoding="utf-8") as fh:
                json.dump(health, fh)
            argv += ["--health-file", health_path]
        return subprocess.run(argv, capture_output=True, text=True,  # noqa: S603
                              encoding="utf-8", errors="replace")

    def test_both_expected_values_empty_fails(self):
        done = self._run_ci(fingerprint="", generation="",
                            health={"evidence": {"fingerprint": "ab" * 32, "generation": 2}})
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("미설정", done.stdout)

    def test_fingerprint_set_generation_empty_fails(self):
        done = self._run_ci(fingerprint="ab" * 32, generation="",
                            health={"evidence": {"fingerprint": "ab" * 32, "generation": 2}})
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("EVIDENCE_PIN_GENERATION", done.stdout)

    def test_generation_set_fingerprint_empty_fails(self):
        done = self._run_ci(fingerprint="", generation="2",
                            health={"evidence": {"fingerprint": "ab" * 32, "generation": 2}})
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("EVIDENCE_PIN_FINGERPRINT", done.stdout)

    def test_whitespace_fingerprint_is_unset(self):
        done = self._run_ci(fingerprint=" ", generation="2",
                            health={"evidence": {"fingerprint": "ab" * 32, "generation": 2}})
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("미설정", done.stdout)                 # truthiness 로 오판하지 않는다

    def test_generation_non_numeric_fails(self):
        done = self._run_ci(fingerprint="ab" * 32, generation="두번째",
                            health={"evidence": {"fingerprint": "ab" * 32, "generation": 2}})
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("숫자가 아닙니다", done.stdout)

    def test_health_url_missing_fails(self):
        done = self._run_ci(fingerprint="ab" * 32, generation="2", health_url="",
                            health={"evidence": {"fingerprint": "ab" * 32, "generation": 2}})
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("health_url_missing", done.stdout)

    def test_matching_passes(self):
        done = self._run_ci(fingerprint="ab" * 32, generation="2", key_id="abcd1234",
                            health={"evidence": {"fingerprint": "ab" * 32,
                                                 "key_id": "abcd1234", "generation": 2}})
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_mismatch_fails(self):
        done = self._run_ci(fingerprint="ab" * 32, generation="2",
                            health={"evidence": {"fingerprint": "cd" * 32, "generation": 2}})
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("fingerprint_mismatch", done.stdout)

    def test_key_id_mismatch_fails(self):
        done = self._run_ci(fingerprint="ab" * 32, generation="2", key_id="deadbeef",
                            health={"evidence": {"fingerprint": "ab" * 32,
                                                 "key_id": "abcd1234", "generation": 2}})
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("key_id_mismatch", done.stdout)

    def test_workflow_variable_names_match_pin_variables(self):
        """워크플로의 `vars.NAME` 이 핀 변수 이름과 일치해야 한다(오타·이름 갈라짐 방지)."""
        _private, public = C.keypair()
        pin_path = os.path.join(self.dir, "pin.json")
        pins.write(pin_path, pins.make(public, C.fingerprint(public), C.key_id(public).hex(),
                                       generation=1, health_url="https://example.test"))
        pin_names = set(commands.pin_variables(pin_path).keys())
        with open(WORKFLOW, encoding="utf-8") as fh:
            text = fh.read()
        used = set(re.findall(r"vars\.([A-Z0-9_]+)", text))
        allowed = pin_names | {"EVIDENCE_CI_SCRIPT_SHA"}     # CI 전용: 검증 스크립트 해시
        self.assertLessEqual(used, allowed,
                             "워크플로가 모르는 vars 이름을 쓴다: %s" % sorted(used - allowed))
        for name in ("EVIDENCE_PIN_FINGERPRINT", "EVIDENCE_PIN_GENERATION",
                     "EVIDENCE_PIN_KEY_ID", "EVIDENCE_PIN_HEALTH_URL", "EVIDENCE_CI_SCRIPT_SHA"):
            self.assertIn(name, used)
        self.assertNotIn("pull_request.head.sha", text)      # PR 작성자가 검증 코드를 공급하지 않는다


if __name__ == "__main__":
    unittest.main()
