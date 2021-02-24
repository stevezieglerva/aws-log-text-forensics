import argparse
import glob
import os
from subprocess import call
import re
import json
from datetime import datetime

import matplotlib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from StackedDateHistogram import StackedDateHistogram
from Histogram import Histogram


PERIOD_FORMAT_HOURS = "H"
PERIOD_FORMAT_MINS = "min"
PERIOD_FORMAT_SECS = "S"


def include_log(args, log):
    if re.findall(args.log, log, flags=re.I):
        if args.log_exclude != "":
            if re.findall(args.log_exclude, log, flags=re.I):
                return False
        return True
    return False


def main(args):
    start = datetime.now()
    all_logs = glob.glob("logs/**/*.*", recursive=True)
    filtered_logs = []
    for log in all_logs:
        if include_log(args, log):
            filtered_logs.append(log)

    log_count = len(filtered_logs)
    print(f"Found logs:    {log_count:>14,}")
    output = "tmsp,log,message,count\n"
    match_counts = 0
    read_lines = 0
    read_bytes = 0
    empty_files_to_remove = []
    for log_count, local_log in enumerate(filtered_logs):
        if log_count % 1000 == 0 and log_count > 0:
            print(f"\t{log_count}")
        with open(local_log, "r") as file:
            lines = file.readlines()
            lines_in_log = len(lines)
            if lines_in_log == 0:
                empty_files_to_remove.append(local_log)
            read_lines = read_lines + len(lines)
            for line in lines:
                read_bytes = read_bytes + len(line)
                tmsp, log, message = split_fields_from_line(line)
                if tmsp is None:
                    continue
                if is_match(tmsp, message, args):
                    match_counts = match_counts + 1
                    output = output + f'{tmsp},"{log}","{message}",1\n'
    output = output.strip()
    print(f"Read lines:    {read_lines:>14,}")
    print(f"Read bytes:    {read_bytes:>14,}")
    found_emoji = "✅"
    if match_counts == 0:
        found_emoji = "❌"
    print(f"Found matches: {match_counts:>14,} {found_emoji}")
    with open("search_results.csv", "w") as csv:
        csv.write(output)
    end = datetime.now()
    duration = end - start
    print(f"Seconds:       {duration.seconds:>14,}")

    if match_counts == 0:
        quit()

    df = pd.read_csv("search_results.csv")

    df["new_date"] = pd.to_datetime(df["tmsp"], format="%Y-%m-%dT%H:%M:%S")

    min_date = df["new_date"].min()
    max_date = df["new_date"].max()
    date_range = max_date - min_date
    print(f"Data from {min_date} to {max_date} ({date_range})")
    period = get_chart_period_size(min_date, max_date)
    period_column_name = get_column_name_from_period(period)

    df[period_column_name] = pd.to_datetime(
        df["tmsp"], format="%Y-%m-%dT%H:%M:%S"
    ).dt.to_period(period)

    hist = StackedDateHistogram(period_column_name, "log", "count", df)
    hist.set_aggregation("count")
    hist.set_chart_type("bar")
    hist.save_plot("search_date_histogram.png")

    hist_counts = Histogram("log", "count", df)
    hist_counts.set_max_groupings(10)
    hist_counts.set_chart_type("barh")
    hist_counts.save_plot("log_counts.png")

    print("Creating treemap")
    create_treemap(df)

    print("Creating html")
    html = ""
    with open("search_results.html", "w") as file:
        search_terms = args.message
        html = f"<title>'{search_terms}'</title>\n"
        html = (
            html
            + f"<h1>Searched for '{search_terms}' - {match_counts:,} matches </h1>\n"
        )
        html = html + f"exclude: {args.exclude}<br/>"
        html = html + f"tmsp: {args.tmsp}<br/>"
        html = html + f"log: {args.log}<br/>"
        html = html + f"log_exclude: {args.log_exclude}<br/>"
        html = html + "<img width='600px' src='search_date_histogram.png'/>\n"
        html = html + "<img width='600px' src='log_counts.png'/>\n"
        html = html + "<a href='treemap_big.png'><img src='treemap.png'/></a>\n"
        html = html + "<br/><br/><h2>Sample matches from logs</h2>\n"

        grouped_by_log = df.groupby("log")
        matching_log_count = len(grouped_by_log.groups)
        max_samples_per_log = 5
        if matching_log_count <= 50:
            max_samples_per_log = 10
        if matching_log_count <= 5:
            max_samples_per_log = 25
        if matching_log_count <= 2:
            max_samples_per_log = 500
        for key, item in grouped_by_log:
            count = 0
            current_df = grouped_by_log.get_group(key)
            # print(current_df.head(), "\n\n")
            html = html + f"\n<h3>{key}</h3>\n"
            html = html + "<table rules='all' border='1px' width='100%'>\n"
            for index, row in current_df.iterrows():
                count = count + 1
                # html = html + row["message"] + "<br/>"
                message = row["message"]
                if search_terms != ".*":
                    message = re.sub(
                        "(" + search_terms + ")",
                        r"<span style='color: red; background-color:gold'>\1</span>",
                        message,
                        flags=re.I,
                    )
                message = re.sub(
                    "([0-9]+)",
                    r"<span style='color: green'>\1</span>",
                    message,
                    flags=re.I,
                )
                message = re.sub(
                    '("[^"]+")',
                    r"<span style='color: red'>\1</span>",
                    message,
                    flags=re.I,
                )
                log = row["log"]
                tmsp = row["tmsp"].replace("T", " ")
                log = log.replace("/", "/ ")
                row_html = f"<tr><td width='150px'>{tmsp}</td><td  width='300px'>{log}</td><td>{message}</td></tr>\n"
                html = html + row_html
                if count >= max_samples_per_log:
                    break
            html = html + "</table>\n"
        file.write(html)
        url = "file://" + os.getcwd() + "/search_results.html"
        print(url)

    empty_log_count = len(empty_files_to_remove)
    for file in empty_files_to_remove:
        os.remove(file)
    print(f"Removed empty logs: {empty_log_count}")


def get_chart_period_size(min_date, max_date):
    max_increments = 6
    hours_limit = 60 * 60 * max_increments
    mins_limit = 60 * max_increments
    duration = max_date - min_date
    if duration.total_seconds() >= hours_limit:
        return PERIOD_FORMAT_HOURS
    if duration.seconds >= mins_limit:
        return PERIOD_FORMAT_MINS
    return PERIOD_FORMAT_SECS


def get_column_name_from_period(period):
    if period == PERIOD_FORMAT_HOURS:
        return "hours"
    if period == PERIOD_FORMAT_MINS:
        return "minutes"
    return "seconds"


def is_match(tmsp, message, args):
    if tmsp is None or tmsp == "":
        return False
    if (
        "T" in tmsp
        and re.findall(args.tmsp, tmsp, flags=re.I)
        and re.findall(args.message, message, flags=re.I)
    ):
        if args.exclude != "":
            if re.findall(args.exclude, message, flags=re.I):
                return False
        return True


def split_fields_from_line(line):
    if re.findall("^/", line):
        words = line.split(" ")
        if len(words) >= 3:
            log_name = words[0].strip()
            tmsp = words[2].strip()
            tmsp_with_microseconds = tmsp[:-5]
            first_words = words[0] + " " + words[1] + " " + words[2]
            message = line.replace(first_words, "").strip().replace('"', "'")
            return (tmsp_with_microseconds, log_name, message)
    return (None, None, None)


def create_treemap(df):
    treemap_data = df.groupby("log")["count"].sum().to_frame().reset_index()
    treemap_data["all"] = "all"
    treemap_data["path1"] = "-"
    treemap_data["path2"] = "-"
    treemap_data["path3"] = "-"
    treemap_data["log_short"] = "-"

    for i in treemap_data.index:
        count = treemap_data.at[i, "count"]
        log = treemap_data.at[i, "log"]
        path1 = "."
        path2 = "."
        path3 = "."
        path_parts = log.split("/")
        if len(path_parts) >= 2:
            path1 = path_parts[1]
        if len(path_parts) >= 3:
            path2 = path_parts[2]
        if len(path_parts) >= 4:
            path3 = path_parts[3]

        log_short = log
        if len(path_parts) >= 4:
            log_short = (
                log.replace(path1, "")
                .replace(path2, "")
                .replace(path3, "")
                .replace("///", "")
            )

        treemap_data.at[i, "log_short"] = log_short
        treemap_data.at[i, "path1"] = path1
        treemap_data.at[i, "path2"] = path2
        treemap_data.at[i, "path3"] = path3
    layout = go.Layout(autosize=False, width=1000, height=1000)
    fig = px.treemap(
        treemap_data,
        path=["all", "path1", "path2", "path3", "log_short"],
        values="count",
    )
    fig.write_image("treemap.png", scale=1)
    fig.write_image("treemap_big.png", scale=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search through downloaded AWS CloudWatch logs"
    )
    parser.add_argument(
        "message",
        type=str,
        default=".*",
        help="regex filter for the message",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default="",
        help="regex filter to exclude the message",
    )
    parser.add_argument(
        "--tmsp",
        type=str,
        default=".*",
        help="regex filter for the timestamp column",
    )
    parser.add_argument(
        "--log",
        type=str,
        default="logs/**/*.*",
        help="glob filter for the log column",
    )
    parser.add_argument(
        "--log-exclude",
        type=str,
        default="",
        help="regex filter to exclude log column",
    )

    args = parser.parse_args()
    print(args)
    main(args)
