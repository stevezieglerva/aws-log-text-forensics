import unittest
from unittest.mock import MagicMock, Mock, PropertyMock, patch

from search_logs import *


class ForensicsUnitTests(unittest.TestCase):
    def test_count_matched_word_patterns__given_line__then_results_correct(self):
        # Arrange
        match_re = r"hello|my|o[^ ]+"
        input = "hello there my old friend, Ollie"

        # Act
        results = count_matched_word_patterns(match_re, input)
        print(results)

        # Assert
        self.assertEqual(
            results,
            [
                PatternMatch(pattern="hello", matches=["hello"], count=1),
                PatternMatch(pattern="my", matches=["my"], count=1),
                PatternMatch(pattern="o[^ ]+", matches=["old", "Ollie"], count=2),
            ],
        )


if __name__ == "__main__":
    unittest.main()
