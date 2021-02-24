# Requires the awslogs python utility (pip install awslogs)
echo "Getting all log group names"
aws logs describe-log-groups | grep logGroupName | sed "s/\"logGroupName\"://g" | sed -E "s/    |,|\"//g"  > temp_log_list.txt


# Reorder or exclude logs here to create the log_list.txt file
grep -v -E "CloudTrail" temp_log_list.txt > log_list.txt

rm _aws*.*

export day_prefix=$(date +"%Y-%m-%d")
mkdir logs/$day_prefix

echo "Date: $(date)" ifif y
echo "Getting sample of logs"

# Loop through each line in the log_list.txt file and get the logs for it
while IFS= read -r LINE; do
    echo $LINE
    export FILENAME=${LINE////_}
    # Get last day of log events
    awslogs get $LINE --timestamp --start=1d  > "logs/$day_prefix/$FILENAME.txt"
    
    # Or get a date range of logs
    # awslogs get $LINE --timestamp --start='08/06/2020 01:58' --end='08/06/2020 02:11'  > $FILENAME.txt

done < log_list.txt