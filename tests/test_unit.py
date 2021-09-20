import unittest
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pandas as pd
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

    def test_create_pattern_datehistogram__given_data__then_plot_saved(self):
        # Arrange
        df = pd.read_csv("tests/search_results_by_pattern.csv")
        period_column_name = add_new_date_columns(df)
        print(period_column_name)
        print(df)

        # Act
        results = create_pattern_datehistogram(df, period_column_name)

        # Assert
        self.assertEqual(results, "plot_x.png")


if __name__ == "__main__":
    unittest.main()
