# Manual filter of logs to retrieve
export log_group_filter="ZillowParseIndividualHTMLFuncti"
export duration="2h"
#export log_group_terms_filter="?START ?END ?line ?url ?ERROR ?processed ?s3 ?key ?Skipping ?Adding"



# Requires the awslogs python utility (pip install awslogs)
echo "Getting all log group names matching: $log_group_filter"
aws logs describe-log-groups | grep logGroupName | sed "s/\"logGroupName\"://g" | sed -E "s/    |,|\"//g"  > temp_log_list.txt


# Filter log names to manual pattern
grep  -E "$log_group_filter" temp_log_list.txt > temp_manual_filter_log_list.txt


# Reorder or exclude logs here to create the log_list.txt file
grep -v -E "CloudTrail" temp_manual_filter_log_list.txt > log_list.txt


export day_prefix=$(date +"%Y-%m-%d")
mkdir logs/temp
rm logs/temp/*.*

echo "Date: $(date)"
echo "Getting sample of logs"

# Loop through each line in the log_list.txt file and get the logs for it
while IFS= read -r LINE; do
    echo $LINE
    export FILENAME=${LINE////_}
    # Get last day of log events
    awslogs get $LINE --timestamp --start $duration   > "logs/temp/$FILENAME.txt"
    
    # Or get a date range of logs
    # awslogs get $LINE --timestamp --start='08/06/2020 01:58' --end='08/06/2020 02:11'  > $FILENAME.txt

done < log_list.txt

# Partition the logs by hour
python3 partition_logs.py 

