# aws-log-text-forensics 🔎

Set of scripts to download CloudWatch logs locally and perform forensics searching. This is a slower, cheaper alternative to real continuous monitoring tools like ELK and Splunk. Those tools are recommended for any medium to large system. But, for small accounts without any log monitoring, this can be a decent alternartive to investigate incidents. The process creates an HTML page with some charts visualizing the matches and a sample of matched log lines.

After the logs are downloaded, they can be searched via a Python command line. The command below will search all logs whose path match the "2021-02-14.*ec2" regex (but exclude "httpd" logs), occurring from 08:00:00 through 10:59:00, looking for lines with the word "error" but not "no errors found."

```
 > python3 search_logs.py --log "2021-02-14.*ec2" --log-exclude "httpd" --tmsp "T(08|09|10)" --exclude "no errors found" "error"

Namespace(exclude='', log='gw', log_exclude='ops-aws', message="\\+1[0-9]+'", tmsp='.*')
Found logs:                63
Read lines:           595,717
Read bytes:       266,181,010
Found matches:          1,121 ✅
Seconds:                    9
Data from 2021-02-22 21:42:01 to 2021-02-23 21:36:01 (0 days 23:54:00)
Creating treemap
Creating html
file:///Users/sziegler/Documents/GitHub/aws-log-text-forensics/search_results.html
Removed empty logs: 0
```

Here is another search with images of the resulting charts:
```
> python3 search_logs.py --log "svz.*ops"    "error"

Namespace(exclude='', log='svz.*ops', log_exclude='', message='error', tmsp='.*')
Found logs:                 8
Read lines:         1,660,867
Read bytes:       245,063,286
Found matches:         18,589 ✅
Seconds:                   18
Data from 2021-02-23 02:40:34 to 2021-02-24 02:45:39 (1 days 00:05:05)
Creating treemap
Creating html
file:///Users/sziegler/Documents/GitHub/aws-log-text-forensics/search_results.html
Removed empty logs: 0
```

![](docs/search_date_histogram.png)
![](docs/log_counts.png)
![](docs/treemap.png)
![](docs/sample_log_lines.png)
## Pre-reqs
- Python3
- AWS CLI
- [awslogs](https://github.com/jorgebastida/awslogs) 
- Install the requirements
```
pip install -r requirements.txt
```


## Usage
```
usage: search_logs.py [-h] [--exclude EXCLUDE] [--tmsp TMSP] [--log LOG]
                      [--log-exclude LOG_EXCLUDE]
                      message
```

* message - required regex to match the log lines
* excluded - optional regex to exclude the log lines
* log - optional regex to filter the logs processed. Defaults to "partitioned" to include all logs in logs/partitioned
* log-exclude - optional regex to exclude the logs processed. Defaults to "" to include all logs in logs/


## Getting started
### Download recent logs
- Run the [get_all_logs.sh](get_all_logs.sh) script to download the last 24 hours of logs. Depending on the number and size of the logs, it could take over an hour to run. It will try to download all log groups, even those that have not been updated recently. The logs will be put into the logs/<date>/ directory. 
```
> . get_all_logs.sh
Getting all log group names
mkdir: logs/2021-02-24: File exists
Date: Wed Feb 24 13:12:11 EST 2021 ifif y
Getting sample of logs
/aws-glue/crawlers
/aws/aes/domains/ziegler-es-2019/application-logs
/aws/aes/domains/ziegler-es-2019/search-logs
/aws/aes/domains/ziegler-es/application-logs
/aws/codebuild/cloudtrail
/aws/codebuild/cloudtrail-log-analytics
...
```
- To keep exports organized, you can create new directories unders logs/ to group files by AWS account or incident. The tool will search any files under logs/. 

### Search the logs
Do an empty search to see the metrics for all logs. Any empty log files encountered will be removed at the end of processing. All paramterrs take regex expressions.
```
> python3 search_logs.py ""
```

Open the resulting search_results.html to see the charts and sample matches.

![](docs/html_sample.png)



Search for "error"
```
> python3 search_logs.py "error"
```

Search for "error" but exclude the false positive for "ops-aws-fake-cw-errors-new"
```
> python3 search_logs.py "error" --exclude "ops-aws-fake-cw-errors-new"
```

Search for "error", but exclude the false positive for "ops-aws-fake-cw-errors-new", and exclude the log for "ops-aws-analyze-metrics-frequency"
```
> python3 search_logs.py "error" --exclude "ops-aws-fake-cw-errors-new" --log-exclude "ops-aws-analyze-metrics-frequency"
```

Search for "error", exclude the false positive for "ops-aws-fake-cw-errors-new", exclude the log for "ops-aws-analyze-metrics-frequency", and search for the :05 minute mark of 09:00, 10:00, or 11:00.
```
 python3 search_logs.py "error" --exclude "ops-aws-fake-cw-errors-new" --log-exclude "ops-aws-analyze-metrics-frequency" tmsp="T(09|10|11):05"
 ```


