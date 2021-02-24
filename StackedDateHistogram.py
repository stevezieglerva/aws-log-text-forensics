import json

import pandas as pd
import matplotlib.pyplot as plt


class StackedDateHistogram:
    def __init__(
        self,
        date_column_name,
        grouping_column,
        value_column,
        df,
    ):
        self._max_groupings = 5
        self._date_column_name = date_column_name
        self._grouping_column = grouping_column
        self._value_column = value_column
        self._aggregation = "sum"
        self._chart_type = "area"
        self._input_df = df
        plt.style.use("seaborn")

    def set_max_groupings(self, max_groupings):
        self._max_groupings = max_groupings

    def set_aggregation(self, aggregation):
        possible_values = ["sum", "count"]
        assert (
            aggregation in possible_values
        ), f"aggregation must be one of: {possible_values}"
        self._aggregation = aggregation

    def set_chart_type(self, chart_type):
        possible_values = ["area", "bar"]
        assert (
            chart_type in possible_values
        ), f"chart_type must be one of: {possible_values}"
        self._chart_type = chart_type

    def _group_data(self, period_grouping=""):
        largest_df = (
            self._input_df.groupby([self._grouping_column])[self._value_column]
            .sum()
            .nlargest(self._max_groupings)
            .to_frame()
        )
        largest_categories = largest_df.index.values.tolist()
        # print(largest_categories)
        filtered_to_largest = self._input_df[
            self._input_df[self._grouping_column].isin(largest_categories)
        ]

        if self._aggregation == "sum":
            new_group = filtered_to_largest.groupby(
                [self._date_column_name, self._grouping_column]
            )[self._value_column].sum()
        if self._aggregation == "count":
            new_group = filtered_to_largest.groupby(
                [self._date_column_name, self._grouping_column]
            )[self._value_column].count()
        return new_group

    def to_json(self):
        self._grouped_df = self._group_data().unstack()
        json_str = self._grouped_df.to_json()
        json_dict = json.loads(json_str)
        return json_dict

    def save_plot(self, filename, period_grouping=""):
        fig, ax = plt.subplots()
        self._grouped_df = self._group_data().unstack()
        self._grouped_df.plot(kind=self._chart_type, stacked=True, width=0.8, ax=ax)
        plt.xticks(rotation=90)
        # ax.set_axisbelow(True)
        # ax.grid(linestyle="-", linewidth="0.25", color="lightgray")
        plt.tight_layout()
        plt.savefig(filename)
