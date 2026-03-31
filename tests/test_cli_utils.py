import unittest
from unittest.mock import Mock, patch

from cli import utils


class CliUtilsTests(unittest.TestCase):
    def test_get_ticker_exits_cleanly_when_prompt_cancelled(self):
        prompt = Mock()
        prompt.ask.return_value = None

        with patch.object(utils.questionary, "text", return_value=prompt), patch.object(
            utils.console, "print"
        ):
            with self.assertRaises(SystemExit) as ctx:
                utils.get_ticker()

        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
