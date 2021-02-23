import argparse
import glob
import os
from subprocess import call
import re
from datetime import datetime

import matplotlib
import pandas as pd

from StackedDateHistogram import StackedDateHistogram


PERIOD_FORMAT_HOURS = "H"
PERIOD_FORMAT_MINS = "min"
PERIOD_FORMAT_SECS = "S"


def main(args):
    start = datetime.now()
    matching_logs = glob.glob(args.log, recursive=True)
    log_count = len(matching_logs)
    print(f"Found logs:    {log_count:>14,}")
    output = "tmsp,log,message,count\n"
    match_counts = 0
    read_lines = 0
    read_bytes = 0
    for log in matching_logs:
        with open(log, "r") as file:
            lines = file.readlines()
            read_lines = read_lines + len(lines)
            for line in lines:
                read_bytes = read_bytes + len(line)
                tmsp, log, message = split_fields_from_line(line)
                if tmsp is None:
                    continue
                if (
                    re.findall("T[0-9]", tmsp, flags=re.I)
                    and re.findall(args.tmsp, tmsp, flags=re.I)
                    and re.findall(args.message, message, flags=re.I)
                ):
                    match_counts = match_counts + 1
                    output = output + f'{tmsp},"{log}","{message}",1\n'
    output = output.strip()
    print(f"Read lines:    {read_lines:>14,}")
    print(f"Read bytes:    {read_bytes:>14,}")
    print(f"Found matches: {match_counts:>14,}")
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
    print(f"Data from {min_date} to {max_date} ({duration})")
    period = get_chart_period_size(min_date, max_date)

    df["new_date_period"] = pd.to_datetime(
        df["tmsp"], format="%Y-%m-%dT%H:%M:%S"
    ).dt.to_period(period)

    hist = StackedDateHistogram("new_date_period", "log", "count", df)
    hist.set_aggregation("count")
    hist.set_chart_type("bar")
    hist.save_plot("search_date_histogram.png")

    html = ""
    with open("search_results.html", "w") as file:
        search_terms = args.message
        html = f"<title>'{search_terms}'</title>"
        html = f"<h1>'{search_terms}'</h1>"
        html = html + "<img  src='search_date_histogram.png'/>\n"
        count = 0
        html = html + "<table rules='all' border='1px' width='100%'>"
        for index, row in df.iterrows():
            count = count + 1
            # html = html + row["message"] + "<br/>"
            message = row["message"]
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
            row_html = f"<tr><td>{tmsp}</td><td>{log}</td><td>{message}</td></tr>\n"
            html = html + row_html
            if count >= 1000:
                break
        html = html + "</table>"
        file.write(html)
        url = "file://" + os.getcwd() + "/search_results.html"
        print(url)


def get_chart_period_size(min_date, max_date):
    max_increments = 6
    hours_limit = 60 * 60 * max_increments
    mins_limit = 60 * max_increments
    duration = max_date - min_date
    if duration.seconds >= hours_limit:
        return PERIOD_FORMAT_HOURS
    if duration.seconds >= mins_limit:
        return PERIOD_FORMAT_MINS
    return PERIOD_FORMAT_SECS


def split_fields_from_line(line):
    words = line.split(" ")
    if len(words) >= 3:
        log_name = words[0].strip()
        tmsp = words[2].strip()
        tmsp_with_microseconds = tmsp[:-5]
        first_words = words[0] + " " + words[1] + " " + words[2]
        message = line.replace(first_words, "").strip().replace('"', "'")
        return (tmsp_with_microseconds, log_name, message)
    return (None, None, None)


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

    args = parser.parse_args()
    print(args)
    main(args)
