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
        self.assertEqual(results, "search_date_histogram_by_pattern.png")

    def test_split_fields_from_line__given_standard_cw_line__then_results_correct(self):
        # Arrange
        input = '/aws/lambda/zillow-and-schools-ZillowParseIndividualHTMLFuncti-14FEP2JCS43HC 2021/09/22/[$LATEST]83957b117bb64a47b39b4550425ee62a 2021-09-22T00:01:03.996Z "eventSource": "aws:s3",'

        # Act
        results = split_fields_from_line(input)
        print(f"test results: {results}")

        # Assert
        self.assertEqual(
            results,
            (
                "2021-09-22T00:01:03",
                "/aws/lambda/zillow-and-schools-ZillowParseIndividualHTMLFuncti-14FEP2JCS43HC",
                "'eventSource': 'aws:s3',",
            ),
        )


if __name__ == "__main__":
    unittest.main()
