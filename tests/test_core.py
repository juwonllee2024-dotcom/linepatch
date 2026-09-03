from __future__ import annotations

import unittest

from linepatch.core import repair_text


class RepairTextTests(unittest.TestCase):
    def test_reflows_wrapped_prose_keeps_boundaries(self) -> None:
        result = repair_text(
            "This is a wrapped\nparagraph that continues.\n\n"
            "A complete sentence.\nA new sentence.\n"
        )

        self.assertEqual(
            "This is a wrapped paragraph that continues.\n\n"
            "A complete sentence.\nA new sentence.\n",
            result.text,
        )
        self.assertEqual(1, result.joined_lines)

    def test_repairs_a_word_split_at_a_line_hyphen(self) -> None:
        result = repair_text("The inter-\nnational standard is useful.\n")

        self.assertEqual("The international standard is useful.\n", result.text)
        self.assertEqual(1, result.dehyphenated_words)

    def test_normalizes_common_copy_artifacts(self) -> None:
        result = repair_text("A\u00a0word.\r\nwith a soft\u00adhyphen.\r\n")

        self.assertEqual("A word.\nwith a softhyphen.\n", result.text)
        self.assertGreaterEqual(result.normalized_artifacts, 2)

    def test_preserves_lists_headings_code_urls_and_email_lines(self) -> None:
        raw = (
            "# Release notes\n"
            "- Keep this item\n"
            "- Keep that item\n"
            "https://example.com/a\n"
            "support@example.com\n"
            "```python\n"
            "value = 1\n"
            "print(value)\n"
            "```\n"
        )

        result = repair_text(raw)

        self.assertEqual(raw, result.text)
        self.assertEqual(0, result.joined_lines)

    def test_change_summary_is_empty_for_clean_text(self) -> None:
        result = repair_text("Already clean.\n\nDone.\n")

        self.assertEqual(result.input_text, result.text)
        self.assertFalse(result.changed)
        self.assertEqual(0, result.change_count)


if __name__ == "__main__":
    unittest.main()
