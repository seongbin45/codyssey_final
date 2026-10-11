"""GEMINI_THINKING_BUDGET: 비우면 기존 동작, 0 이면 thinking 끔, 모델이 거부하면 한 번만 끄고 계속."""
import os
import unittest

from app import gemini as ai


class Resp:
    text = '{"ok": true}'


class FakeModels:
    def __init__(self, reject_thinking=False):
        self.configs, self.reject = [], reject_thinking

    def generate_content(self, model, contents, config):
        self.configs.append(config)
        if self.reject and getattr(config, "thinking_config", None) is not None:
            raise RuntimeError("400 INVALID_ARGUMENT: Budget 0 is invalid. This model only works in thinking mode.")
        return Resp()


class FakeClient:
    def __init__(self, **kw):
        self.models = FakeModels(**kw)


class ThinkingTest(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.get("GEMINI_THINKING_BUDGET"); ai._thinking_rejected = False

    def tearDown(self):
        os.environ.pop("GEMINI_THINKING_BUDGET", None)
        if self._env is not None: os.environ["GEMINI_THINKING_BUDGET"] = self._env
        ai._thinking_rejected = False

    def test_unset_changes_nothing(self):
        os.environ.pop("GEMINI_THINKING_BUDGET", None)
        c = FakeClient(); ai.generate_text(c, "m", "p", temperature=0.7)
        self.assertIsNone(c.models.configs[0].thinking_config)

    def test_budget_zero_is_sent(self):
        os.environ["GEMINI_THINKING_BUDGET"] = "0"
        c = FakeClient(); ai.generate_text(c, "m", "p")
        self.assertEqual(c.models.configs[0].thinking_config.thinking_budget, 0)

    def test_invalid_value_is_ignored(self):
        os.environ["GEMINI_THINKING_BUDGET"] = "abc"
        c = FakeClient(); ai.generate_text(c, "m", "p")
        self.assertIsNone(c.models.configs[0].thinking_config)

    def test_rejected_once_then_not_sent_again(self):
        os.environ["GEMINI_THINKING_BUDGET"] = "0"
        c = FakeClient(reject_thinking=True)
        self.assertEqual(ai.generate_text(c, "m", "p"), '{"ok": true}')          # 거부 → 같은 시도를 설정 없이 다시 해서 성공
        self.assertEqual(len(c.models.configs), 2)
        ai.generate_text(c, "m", "p")                                            # 다음부터는 처음부터 보내지 않는다
        self.assertEqual(len(c.models.configs), 3)
        self.assertTrue(ai._thinking_rejected)

    def test_unrelated_error_is_not_swallowed(self):
        os.environ["GEMINI_THINKING_BUDGET"] = "0"
        class Boom(FakeModels):
            def generate_content(self, model, contents, config): raise RuntimeError("503 UNAVAILABLE")
        c = FakeClient(); c.models = Boom()
        with self.assertRaises(RuntimeError): ai.generate_text(c, "m", "p")
        self.assertFalse(ai._thinking_rejected)


if __name__ == "__main__":
    unittest.main()
