import glob
import os
import re


def main():
    print("Removing old partitioned files")
    remove_files = glob.glob("logs/partitioned/*.*")
    for remove_file in remove_files:
        os.remove(remove_file)

    temp_files = glob.glob("logs/temp/*.*")
    downloaded_logs = len(temp_files)
    print(f"Logs to partition: {downloaded_logs:>10,}")
    total_lines = 0
    file_count = 0
    for local_log in temp_files:
        file_count = file_count + 1
        if file_count % 10 == 0:
            print(f"\tProcessed {file_count} logs with {total_lines:,}")
        with open(local_log, "r") as file:
            print(local_log)
            lines = file.readlines()
            new_lines = {}
            for line in lines:
                total_lines = total_lines + 1
                tmsp, log, message = split_fields_from_line(line)
                print(tmsp, log)
                if tmsp != None:
                    tmsp_partition = tmsp.replace(":", "")
                    hour_partition = tmsp_partition[0:13]
                    log_esc = log.replace("/", "_")
                    new_filename = f"logs/partitioned/{log_esc}_{hour_partition}.txt"
                    if new_filename in new_lines:
                        current_lines = new_lines[new_filename]
                        current_lines.append(line)
                        new_lines[new_filename] = current_lines
                    else:
                        new_lines[new_filename] = [line]
            print(new_lines)
            for partition_log_name in new_lines:
                print(partition_log_name)
                with open(partition_log_name, "w") as partition:
                    partition.writelines(new_lines[partition_log_name])
    print(f"Read lines: {total_lines:>10,}")


def split_fields_from_line(line):
    if re.findall("^/", line):
        words = line.split(" ")
        if len(words) >= 3:
            log_name = words[0].strip()
            tmsp = words[2].strip()
            tmsp_without_microseconds = tmsp[:-5]
            first_words = words[0] + " " + words[1] + " " + words[2]
            message = line.replace(first_words, "").strip().replace('"', "'")
            return (tmsp_without_microseconds, log_name, message)
    return (None, None, None)


if __name__ == "__main__":
    main()
