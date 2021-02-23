import argparse
import glob
import os
import re

import matplotlib
import pandas as pd

from StackedDateHistogram import StackedDateHistogram


def main(args):
    matching_logs = glob.glob(args.log)
    log_count = len(matching_logs)
    print(f"Found matching logs: {log_count}")
    output = "tmsp,log,message,count\n"
    match_counts = 0
    for log in matching_logs:
        with open(log, "r") as file:
            lines = file.readlines()
            for line in lines:
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
    match_counts
    print(f"Found matches: {match_counts}")
    with open("search_results.csv", "w") as csv:
        csv.write(output)

    df = pd.read_csv("search_results.csv")

    df["new_date_hour"] = pd.to_datetime(
        df["tmsp"], format="%Y-%m-%dT%H:%M:%S"
    ).dt.to_period("H")
    df["new_date_min"] = pd.to_datetime(
        df["tmsp"], format="%Y-%m-%dT%H:%M:%S"
    ).dt.to_period("min")

    hist = StackedDateHistogram("new_date_hour", "log", "count", df)
    hist.set_aggregation("count")
    hist.save_plot("search_hour.png")

    hist = StackedDateHistogram("new_date_min", "log", "count", df)
    hist.set_aggregation("count")
    hist.save_plot("search_min.png")

    html = ""
    with open("search_results.html", "w") as file:
        search_terms = args.message
        html = f"<title>'{search_terms}'</title>"
        html = f"<h1>'{search_terms}'</h1>"
        html = html + "<img  src='search_hour.png'/>\n"
        html = html + "<img  src='search_min.png'/>\n"
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
            log = row["log"]
            tmsp = row["tmsp"].replace("T", " ")
            row_html = f"<tr><td>{tmsp}</td><td>{log}</td><td>{message}</td></tr>\n"
            html = html + row_html
            if count >= 1000:
                break
        html = html + "</table>"
        file.write(html)


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
