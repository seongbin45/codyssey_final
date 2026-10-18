"""증거 봉인 훅 — 형식 호환·수집 캡·스크럽·보관·통보·스로틀.

가장 중요한 검사는 **CLI 와의 형식 호환**이다: 앱이 봉인한 것을 관리자 CLI 의 `unseal` 로 실제로 연다.
그래서 이 테스트는 `tools/opsarchive` 를 경로에 넣고 그 구현을 그대로 쓴다(명세가 갈라지면 실패한다).

실행: cd backend && python -m unittest tests.test_evidence
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "opsarchive"))
from opsarchive import container as C          # noqa: E402 — 검증용(앱은 이 패키지를 쓰지 않는다)
from opsarchive import pins as P                # noqa: E402 — 핀/Actions 변수 규약 실측용

from app import evidence                        # noqa: E402


def pack_ed25519(public: bytes) -> str:
    """서명 키 공개 절반을 환경변수 문자열로 (`ed25519:<base64url(no padding)>`)."""
    return "ed25519:" + base64.urlsafe_b64encode(public).decode().rstrip("=")


def pack_x25519(public: bytes) -> str:
    """CLI 핀이 서명 키를 감쌀 때 쓰는 표기(`x25519:` — `pins.make` 가 그렇게 쓴다)."""
    return C.pack_public_key(public)


class SealedCompatibilityTest(unittest.TestCase):
    """앱이 봉인 → CLI 가 해제. 형식(MFA1)이 어긋나면 여기서 깨진다."""

    def setUp(self):
        evidence.reset_state()
        self.private, self.public = C.keypair()
        self.env = mock.patch.dict(os.environ, {
            "EVIDENCE_PUBKEY": C.pack_public_key(self.public),
            "EVIDENCE_KEY_GENERATION": "3",
        }, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_app_seal_is_opened_by_the_cli(self):
        payload = json.dumps({"trigger": "erase_failed", "uid_hash": "abc"}, ensure_ascii=False).encode()
        blob = evidence.seal(payload, evidence.public_key())
        self.assertEqual(C.unseal(blob, self.private), payload)

    def test_cli_seal_is_readable_by_the_app(self):
        """반대 방향도 확인한다(관리자가 만든 것은 없지만, 형식이 대칭임을 고정한다)."""
        payload = b"hello"
        blob = C.seal(payload, self.public)
        # 앱에는 unseal 이 없다 — 개인키를 앱에 두지 않기 때문이다. 대신 헤더 계약을 확인한다.
        self.assertTrue(blob.startswith(evidence.MAGIC))
        self.assertEqual(blob[4], evidence.ALG)
        self.assertEqual(blob[5], evidence.VERSION)
        self.assertEqual(blob[6:14], C.key_id(self.public))

    def test_health_block_exposes_only_public_info(self):
        block = evidence.health_block()
        self.assertEqual(block["generation"], 3)
        self.assertEqual(block["key_id"], C.key_id(self.public).hex())
        self.assertEqual(block["fingerprint"], C.fingerprint(self.public))
        self.assertNotIn("public_key", block)

    def test_disabled_without_key(self):
        with mock.patch.dict(os.environ, {"EVIDENCE_PUBKEY": ""}, clear=False):
            self.assertFalse(evidence.configured())
            self.assertEqual(evidence.health_block(), {})
            self.assertEqual(evidence.seal_and_report("erase_failed")["reason"], "no_key")


class ScrubTest(unittest.TestCase):
    def test_credentials_are_masked(self):
        text = ("Authorization: Bearer abcdefghijklmnop\n"
                "key=AIzaSyA1234567890abcdefghijklmnop\n"
                "pat=github_pat_11ABCDEFG0123456789AB\n"
                "jwt=eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxIn0.abcdef")
        out = evidence.scrub_text(text)
        self.assertNotIn("abcdefghijklmnop", out)
        self.assertNotIn("AIzaSyA1234567890abcdefghijklmnop", out)
        self.assertNotIn("github_pat_11ABCDEFG0123456789AB", out)
        self.assertNotIn("eyJhbGciOiJSUzI1NiJ9", out)
        self.assertIn("[MASKED]", out)

    def test_environment_secret_values_are_masked(self):
        with mock.patch.dict(os.environ, {"SOME_API_TOKEN": "s3cr3t-value-12345"}, clear=False):
            self.assertNotIn("s3cr3t-value-12345", evidence.scrub_text("token=s3cr3t-value-12345"))

    def test_override_keeps_everything(self):
        with mock.patch.dict(os.environ, {"EVIDENCE_INCLUDE_SECRETS": "1"}, clear=False):
            text = "Bearer abcdefghijklmnop"
            self.assertEqual(evidence.scrub_text(text), text)


class CollectTest(unittest.TestCase):
    def setUp(self):
        evidence.reset_state()

    def test_caps_truncate_source_and_mark_it(self):
        import tempfile
        root = tempfile.mkdtemp(prefix="evidence-src-")
        with open(os.path.join(root, "big.py"), "w", encoding="utf-8") as fh:
            fh.write("x" * 5000)
        with open(os.path.join(root, "small.py"), "w", encoding="utf-8") as fh:
            fh.write("print('hi')\n")
        with mock.patch.dict(os.environ, {"EVIDENCE_MAX_SOURCE_BYTES": "100"}, clear=False):
            report = evidence.collect("erase_failed", source_root=root)
        self.assertIn("source", report)
        self.assertEqual(len(report["source"]["files"]), 2)      # 목록은 다 남는다(크기만 잘림)
        self.assertTrue(report["truncated"].get("source"))
        self.assertLessEqual(len(json.dumps(report["source"]["content"], ensure_ascii=False)), 200)

    def test_logs_are_capped(self):
        for index in range(30):
            evidence._ring.records.append("line-%d-%s" % (index, "y" * 100))
        with mock.patch.dict(os.environ, {"EVIDENCE_MAX_LOGS_BYTES": "300"}, clear=False):
            report = evidence.collect("erase_failed")
        self.assertTrue(report["truncated"].get("logs"))
        self.assertLess(len(json.dumps(report["logs"])), 400)

    def test_ledger_verification_and_error_are_recorded(self):
        error = ValueError("boom")
        report = evidence.collect("erase_failed", uid="uid-1",
                                  ledger=[{"step": "tombstone", "ok": True, "code": ""}],
                                  verification={"ok": False}, error=error)
        self.assertEqual(report["ledger"][0]["step"], "tombstone")
        self.assertEqual(report["verification"]["ok"], False)
        self.assertEqual(report["error"]["type"], "ValueError")
        self.assertIn("boom", report["error"]["message"])
        self.assertEqual(report["uid_hash"], __import__("hashlib").sha256(b"uid-1").hexdigest()[:16])

    def test_env_values_are_not_collected_only_names(self):
        with mock.patch.dict(os.environ, {"EVIDENCE_PUBKEY": "x25519:AAABBB"}, clear=False):
            report = evidence.collect("erase_failed")
        self.assertIn("EVIDENCE_PUBKEY", report["runtime"]["env_names"])
        self.assertNotIn("x25519:AAABBB", json.dumps(report))


class StoreTest(unittest.TestCase):
    class Admin:
        def __init__(self):
            self.calls = []
            self.head = {}

        def firestore(self, method, subpath, body=None):
            self.calls.append((method, subpath, body))
            return self.head if subpath == "evidence_chain/head" else {}

    def test_chunks_are_written_with_ttl(self):
        admin = StoreTest.Admin()
        from app import firebase_admin
        firebase_admin.set_admin(admin)
        try:
            blob = b"z" * (evidence.CHUNK_BYTES + 10)
            document = evidence.store(blob, {"archive_id": "aid1", "expire_at": 123, "trigger": "t"})
        finally:
            firebase_admin.set_admin(None)
        self.assertEqual(document["chunks"], 2)
        self.assertEqual(document["size"], len(blob))
        paths = [c[1] for c in admin.calls]
        writes = [c[1] for c in admin.calls if c[0] == "PATCH"]
        self.assertEqual(paths[0], "evidence_chain/head")                # 먼저 체인 머리를 읽는다
        self.assertEqual(writes[0], "evidence_archives/aid1")            # 메타가 먼저 쓰인다
        self.assertEqual(writes[1:3], ["evidence_archives/aid1/parts/0", "evidence_archives/aid1/parts/1"])
        self.assertEqual(writes[-1], "evidence_chain/head")              # 마지막에 머리를 옮긴다
        part = admin.calls[2][2]["fields"]
        self.assertEqual(part["seq"]["integerValue"], "0")
        self.assertEqual(part["expire_at"]["integerValue"], "123")
        self.assertEqual(base64.b64decode(part["data"]["stringValue"]), blob[:evidence.CHUNK_BYTES])

    def test_manifest_chains_to_the_previous_head(self):
        admin = StoreTest.Admin()
        admin.head = {"fields": {"seq": {"integerValue": "4"},
                                 "digest": {"stringValue": "prev-digest"}}}
        from app import firebase_admin
        firebase_admin.set_admin(admin)
        try:
            document = evidence.store(b"x", {"archive_id": "aid2", "created_at": 7, "expire_at": 9})
        finally:
            firebase_admin.set_admin(None)
        self.assertEqual(document["seq"], 5)
        self.assertEqual(document["prev_digest"], "prev-digest")
        self.assertEqual(document["schema"], evidence.MANIFEST_SCHEMA)
        # digest 는 **매니페스트 필드만**으로 (prev_digest 포함) 계산된다 → 체인이 된다
        body = {k: v for k, v in document.items()
                if k in ("schema", "archive_id", "created_at", "ciphertext_sha256", "size",
                         "chunks", "recipient_key_id", "trigger", "seq", "prev_digest")}
        self.assertEqual(evidence.manifest_digest(body), document["digest"])
        self.assertNotEqual(evidence.manifest_digest(dict(body, prev_digest="other")), document["digest"])


class NotifyTest(unittest.TestCase):
    class Response(io.BytesIO):
        status = 201

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def test_issue_contains_metadata_only(self):
        seen = {}

        def fake_urlopen(request, timeout=0):
            seen["url"] = request.full_url
            seen["body"] = json.loads(request.data.decode())
            seen["auth"] = request.get_header("Authorization")
            return NotifyTest.Response(b"{}")

        env = {"EVIDENCE_GH_TOKEN": "ghp_" + "x" * 20, "EVIDENCE_GH_REPO": "org/repo"}
        with mock.patch.dict(os.environ, env, clear=False), \
                mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ok = evidence.notify({"archive_id": "aid1", "trigger": "erase_failed", "key_id": "kid",
                                  "sha256": "aa", "size": 10, "chunks": 1, "expire_at": 99,
                                  "ledger": [], "verification": {}})
        self.assertTrue(ok)
        self.assertEqual(seen["url"], "https://api.github.com/repos/org/repo/issues")
        self.assertIn("aid1", seen["body"]["body"])
        self.assertEqual(seen["body"]["labels"], ["evidence-seal"])
        self.assertNotIn("data", seen["body"])          # 본문(암호문)은 이슈로 가지 않는다
        self.assertNotIn("x" * 20, json.dumps(seen["body"]))   # 토큰도 본문에 없다

    def test_missing_token_skips_notification(self):
        with mock.patch.dict(os.environ, {"EVIDENCE_GH_TOKEN": "", "EVIDENCE_GH_REPO": ""}, clear=False):
            self.assertFalse(evidence.notify({"archive_id": "aid1"}))


class ThrottleTest(unittest.TestCase):
    def setUp(self):
        evidence.reset_state()
        self.env = mock.patch.dict(os.environ, {"EVIDENCE_DAILY_CAP": "2",
                                                "EVIDENCE_PER_UID_SECONDS": "3600"}, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(evidence.reset_state)

    def test_same_uid_is_throttled(self):
        self.assertTrue(evidence.throttle_ok("uid-1"))
        self.assertFalse(evidence.throttle_ok("uid-1"))

    def test_daily_cap_applies(self):
        self.assertTrue(evidence.throttle_ok("uid-1"))
        self.assertTrue(evidence.throttle_ok("uid-2"))
        self.assertFalse(evidence.throttle_ok("uid-3"))

    def test_seal_and_report_respects_throttle_and_never_raises(self):
        private, public = C.keypair()
        with mock.patch.dict(os.environ, {"EVIDENCE_PUBKEY": C.pack_public_key(public)}, clear=False):
            with mock.patch.object(evidence, "store", side_effect=RuntimeError("firestore down")):
                first = evidence.seal_and_report("erase_failed", uid="uid-9")
                second = evidence.seal_and_report("erase_failed", uid="uid-9")
        self.assertEqual(first["reason"], "failed")          # 저장 실패를 삼킨다
        self.assertEqual(second["reason"], "throttled")      # 스로틀은 실패와 무관하게 먼저 걸린다


class HealthEndpointTest(unittest.TestCase):
    """/health 가 공개 지문·세대를 노출한다 — 핀 검증(.github/workflows/verify-key-pin.yml)이 이 값을 본다."""

    def test_health_exposes_fingerprint_when_enabled(self):
        from fastapi.testclient import TestClient
        from app import main
        _, public = C.keypair()
        with mock.patch.dict(os.environ, {"EVIDENCE_PUBKEY": C.pack_public_key(public),
                                          "EVIDENCE_KEY_GENERATION": "7"}, clear=False):
            body = TestClient(main.app).get("/health").json()
        self.assertEqual(body["evidence"]["fingerprint"], C.fingerprint(public))
        self.assertEqual(body["evidence"]["generation"], 7)

    def test_health_has_empty_evidence_when_disabled(self):
        from fastapi.testclient import TestClient
        from app import main
        with mock.patch.dict(os.environ, {"EVIDENCE_PUBKEY": ""}, clear=False):
            body = TestClient(main.app).get("/health").json()
        self.assertEqual(body["evidence"], {})


class VerifyErasedTest(unittest.TestCase):
    def setUp(self):
        from app import firebase_admin
        self.firebase_admin = firebase_admin
        firebase_admin.set_admin(None)

    def tearDown(self):
        self.firebase_admin.set_admin(None)

    def _admin(self, tombstone=True, document=None, user=None):
        class Admin:
            def read_tombstone(self, uid):
                return tombstone

            def firestore(self, method, subpath, body=None):
                return document or {}

            def lookup_user(self, uid):
                return user or {}

        return Admin()

    def test_ok_when_all_three_are_gone(self):
        self.firebase_admin.set_admin(self._admin())
        result = self.firebase_admin.verify_erased("uid-1")
        self.assertTrue(result["ok"])
        self.assertTrue(result["document_gone"] and result["account_gone"] and result["tombstone"])

    def test_mismatch_when_document_remains(self):
        self.firebase_admin.set_admin(self._admin(document={"fields": {}}))
        result = self.firebase_admin.verify_erased("uid-1")
        self.assertFalse(result["ok"])
        self.assertFalse(result["document_gone"])

    def test_mismatch_when_account_remains(self):
        self.firebase_admin.set_admin(self._admin(user={"localId": "uid-1"}))
        self.assertFalse(self.firebase_admin.verify_erased("uid-1")["ok"])

    def test_seal_failures_env_can_turn_it_off(self):
        """GUI 마인드맵의 seal_failures 노드가 미는 변수가 실제로 동작해야 한다(죽은 변수 금지)."""
        private, public = C.keypair()
        with mock.patch.dict(os.environ, {"EVIDENCE_PUBKEY": C.pack_public_key(public),
                                          "EVIDENCE_SEAL_FAILURES": "0"}, clear=False):
            result = evidence.seal_and_report("erase_failed", uid="uid-off")
        self.assertEqual(result, {"enabled": False, "reason": "disabled_by_env"})

    def test_seal_failures_env_absent_still_seals(self):
        private, public = C.keypair()
        with mock.patch.dict(os.environ, {"EVIDENCE_PUBKEY": C.pack_public_key(public),
                                          "EVIDENCE_SEAL_FAILURES": "1"}, clear=False), \
                mock.patch.object(evidence, "store", return_value={"archive_id": "a", "size": 1,
                                                                   "chunks": 1}), \
                mock.patch.object(evidence, "notify", return_value=True):
            result = evidence.seal_and_report("erase_failed", uid="uid-on")
        self.assertTrue(result.get("enabled"))

    def test_verification_failure_does_not_raise(self):
        class Broken:
            def read_tombstone(self, uid):
                raise RuntimeError("boom")

        self.firebase_admin.set_admin(Broken())
        result = self.firebase_admin.verify_erased("uid-1")
        self.assertIsNone(result["ok"])
        self.assertEqual(result["error"], "verify_failed")


class SigningFingerprintTest(unittest.TestCase):
    """/health 의 evidence 블록이 **서명 키 지문**을 노출한다 — `EVIDENCE_PIN_SIGNING_FINGERPRINT` 핀과 대조.

    확정 결함: 예전에는 `{key_id, fingerprint, generation}` 만 노출해 Actions 변수
    `EVIDENCE_PIN_SIGNING_FINGERPRINT` 를 아무도 검증에 쓰지 못했고, 공격자가 서명 키를 교체해도
    봉투 지문만 맞으면 통과했다. 이 테스트가 그 구멍을 막는다(서명 지문의 존재·형식·부재 규약).
    """

    def setUp(self):
        evidence.reset_state()
        self.env = mock.patch.dict(os.environ, {
            "EVIDENCE_PUBKEY": C.pack_public_key(C.keypair()[1]),
            "EVIDENCE_KEY_GENERATION": "5",
        }, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(evidence.reset_state)

    def test_fingerprint_matches_the_cli_and_is_lowercase_hex_64(self):
        """앱이 유도한 지문은 CLI `fingerprint()` 와 **문자열 그대로** 같아야 한다(형식 규약)."""
        _, signing_public = C.sign_keypair()
        with mock.patch.dict(os.environ, {"EVIDENCE_SIGNING_PUBKEY": pack_ed25519(signing_public)},
                             clear=False):
            app_fp = evidence.signing_fingerprint()
            block = evidence.health_block()
        self.assertEqual(app_fp, C.fingerprint(signing_public))
        self.assertEqual(block["signing_fingerprint"], app_fp)
        self.assertRegex(app_fp, r"^[0-9a-f]{64}$")            # 소문자 hex 64자
        self.assertEqual(len(app_fp), 64)

    def test_prefix_variants_yield_the_same_fingerprint(self):
        """`ed25519:`·`x25519:`(CLI 핀 표기)·접두어 없는 base64url 이 모두 같은 지문을 준다."""
        _, signing_public = C.sign_keypair()
        bare = base64.urlsafe_b64encode(signing_public).decode().rstrip("=")
        expected = C.fingerprint(signing_public)
        for value in (pack_ed25519(signing_public), pack_x25519(signing_public), bare):
            with mock.patch.dict(os.environ, {"EVIDENCE_SIGNING_PUBKEY": value}, clear=False):
                self.assertEqual(evidence.signing_fingerprint(), expected, value[:12])

    def test_app_fingerprint_equals_the_actions_variable_value(self):
        """실측: `pin --sign-key` 가 만든 핀의 `signing_fingerprint_sha256`(→ Actions 변수 값)와
        앱이 `/health` 로 보고하는 값이 **바이트 단위로 같아야** CI 대조가 성립한다."""
        import tempfile
        from opsarchive import commands
        envelope_public = C.keypair()[1]
        _, signing_public = C.sign_keypair()
        pin = P.make(envelope_public, C.fingerprint(envelope_public), C.key_id(envelope_public).hex(),
                     generation=5, health_url="https://example.test", signing_public=signing_public)
        path = os.path.join(tempfile.mkdtemp(prefix="evidence-sign-pin-"), "evidence-key-pin.json")
        P.write(path, pin)
        actions_vars = commands.pin_variables(path)
        # CLI 핀이 서명 공개키를 담는 표기(`x25519:`)를 그대로 앱 환경변수에 넣어도 같은 지문이 나온다.
        with mock.patch.dict(os.environ,
                             {"EVIDENCE_SIGNING_PUBKEY": pin["signing_public_key"]}, clear=False):
            app_fp = evidence.health_block()["signing_fingerprint"]
        self.assertEqual(app_fp, pin["signing_fingerprint_sha256"])
        self.assertEqual(app_fp, actions_vars["EVIDENCE_PIN_SIGNING_FINGERPRINT"])
        self.assertNotEqual(app_fp, "")                        # 빈 값(가짜 통과) 금지

    def test_field_absent_when_signing_key_not_configured(self):
        """서명 키가 없으면 필드를 넣지 않는다(가짜 값·빈 문자열도 금지)."""
        with mock.patch.dict(os.environ, {"EVIDENCE_SIGNING_PUBKEY": ""}, clear=False):
            block = evidence.health_block()
        self.assertNotIn("signing_fingerprint", block)
        # 기존 필드는 그대로다(회귀 방지): 이름·형식 불변
        self.assertEqual(block["generation"], 5)
        self.assertEqual(block["key_id"], evidence.key_id_hex())
        self.assertRegex(block["fingerprint"], r"^[0-9a-f]{64}$")

    def test_corrupted_signing_key_env_is_skipped_without_crashing(self):
        """손상된 서명 키 환경변수 → 예외 없이 필드 생략, 기존 필드는 정상(요구 (d))."""
        for bad in ("not-base64!!", "ed25519:zzzz", "deadbeef"):   # 잘린/비정상 32B 아님
            with mock.patch.dict(os.environ, {"EVIDENCE_SIGNING_PUBKEY": bad}, clear=False):
                self.assertEqual(evidence.signing_fingerprint(), "")
                block = evidence.health_block()                # 예외를 올리지 않는다
                self.assertNotIn("signing_fingerprint", block)
                self.assertEqual(block["generation"], 5)
                self.assertEqual(block["fingerprint"], evidence.fingerprint())

    def test_existing_fields_names_and_formats_unchanged(self):
        """요구 (c): key_id(16 hex)·fingerprint(64 hex)·generation(int) 의 이름·형식이 불변이다."""
        with mock.patch.dict(os.environ,
                             {"EVIDENCE_SIGNING_PUBKEY": pack_ed25519(C.sign_keypair()[1])},
                             clear=False):
            block = evidence.health_block()
        self.assertRegex(block["key_id"], r"^[0-9a-f]{16}$")
        self.assertRegex(block["fingerprint"], r"^[0-9a-f]{64}$")
        self.assertIsInstance(block["generation"], int)
        self.assertNotIn("public_key", block)                  # 공개키 바이트는 노출하지 않는다


class SigningFingerprintEndpointTest(unittest.TestCase):
    """/health 응답 전체 계약 — 서명 지문이 있을 때만 더해진다(라우트 수준 회귀 방지)."""

    def test_endpoint_reports_signing_fingerprint_when_set(self):
        from fastapi.testclient import TestClient
        from app import main
        _, envelope_public = C.keypair()
        _, signing_public = C.sign_keypair()
        with mock.patch.dict(os.environ, {
            "EVIDENCE_PUBKEY": C.pack_public_key(envelope_public),
            "EVIDENCE_KEY_GENERATION": "9",
            "EVIDENCE_SIGNING_PUBKEY": pack_ed25519(signing_public),
        }, clear=False):
            body = TestClient(main.app).get("/health").json()
        self.assertEqual(body["evidence"]["signing_fingerprint"], C.fingerprint(signing_public))
        self.assertEqual(body["evidence"]["fingerprint"], C.fingerprint(envelope_public))
        self.assertEqual(body["evidence"]["generation"], 9)

    def test_endpoint_omits_signing_fingerprint_when_unset(self):
        from fastapi.testclient import TestClient
        from app import main
        _, envelope_public = C.keypair()
        with mock.patch.dict(os.environ, {
            "EVIDENCE_PUBKEY": C.pack_public_key(envelope_public),
            "EVIDENCE_SIGNING_PUBKEY": "",
        }, clear=False):
            body = TestClient(main.app).get("/health").json()
        self.assertNotIn("signing_fingerprint", body["evidence"])
        self.assertIn("fingerprint", body["evidence"])         # 봉투 지문 계약은 그대로


class SigningKeySideEffectTest(unittest.TestCase):
    """부작용 점검: 서명 키 환경변수는 봉인·영수증·탈퇴 경로에 영향을 주지 않아야 한다.

    기존 커버: `ThrottleTest.test_seal_and_report_respects_throttle_and_never_raises`(저장 실패 삼킴),
    `VerifyErasedTest.test_seal_failures_env_can_turn_it_off`(봉인 끄기), `VerifyErasedTest` 의
    `verify_erased` 4건(탈퇴 사후 검증). 여기서는 **서명 키가 설정된 상태**에서 봉인·영수증이
    그대로임을 고정한다(health_block 변경이 이 경로로 새지 않음을 확인).
    """

    def setUp(self):
        evidence.reset_state()
        self.addCleanup(evidence.reset_state)

    def test_seal_and_receipt_unaffected_by_signing_key_env(self):
        _, envelope_public = C.keypair()
        _, signing_public = C.sign_keypair()
        with mock.patch.dict(os.environ, {
            "EVIDENCE_PUBKEY": C.pack_public_key(envelope_public),
            "EVIDENCE_SIGNING_PUBKEY": pack_ed25519(signing_public),
        }, clear=False), \
                mock.patch.object(evidence, "store", return_value={"archive_id": "a", "size": 1,
                                                                   "chunks": 1,
                                                                   "expire_at": 0}) as store, \
                mock.patch.object(evidence, "notify", return_value=True):
            result = evidence.seal_and_report("erase_failed", uid="uid-sign")
        self.assertTrue(result.get("enabled"))
        # 봉인 문서에는 서명 지문·공개키가 새로 흘러들지 않는다(메타 계약 불변).
        document = store.call_args.args[1]
        self.assertNotIn("signing_fingerprint", document)
        self.assertNotIn("signing_public_key", json.dumps(document))
        # 영수증 계약(서명 없음)도 불변.
        receipt = evidence.receipt_for("chal", {"seq": 1, "digest": "d", "created_at": 2}, "ok")
        self.assertEqual(receipt["challenge"], "chal")
        self.assertNotIn("signature", receipt)


if __name__ == "__main__":
    unittest.main()
