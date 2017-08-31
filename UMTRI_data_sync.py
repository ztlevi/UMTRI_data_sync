import csv, time, datetime, os, imageio
from decimal import Decimal

###############################################################################
#                                   Input                                     #
###############################################################################
video_start_datetime = '07/18/17 14:36:27'
video_end_datetime = '07/18/17 15:01:32'
datalogger_input_path = './118_07182017_DataLogger_01.Csv'
bioharness_input_path = './2017_07_18-14_10_38_Summary.csv'
# just the video directory, program will process all video under the path
video_path = './118_07182017_DVR'


def time2seconds(s_time):
    t = time.strptime(s_time, '%H:%M:%S')
    seconds = datetime.timedelta(
        hours=t.tm_hour, minutes=t.tm_min, seconds=t.tm_sec).total_seconds()
    return seconds


# Use this function to get the last row's timestamp in csv file
def get_last_row(csv_filename):
    with open(csv_filename, 'r') as f:
        lastrow = None
        for lastrow in csv.reader(f):
            pass
        return lastrow


# Create output dir if not exist
if not os.path.exists('./output'):
    os.makedirs('./output')

# Video file ** Change video start time here **
video_start_time = video_start_datetime.split()[1]
video_end_time = video_end_datetime.split()[1]

# Convert the video start time to seconds
video_start_time_seconds = time2seconds(video_start_time)
video_end_time_seconds = time2seconds(video_end_time)

# Datalogger file #############################################################
datalogger_output_path = './output/synced_' + datalogger_input_path[2:]

datalogger_start_time = ''
datalogger_start_time_seconds = 0

# delta time between video_start_time and datalogger_start_time
delta_time_datalogger = 0
with open(datalogger_input_path, 'r') as inp, open(
        datalogger_output_path, 'w', newline='') as out:
    writer = csv.writer(out)
    for line_num, row in enumerate(csv.reader(inp), 1):
        # retrieve the datalogger start time and convert to seconds
        if line_num == 3:
            idx = row[0].find(':')
            cur_time = row[0][idx + 1:].strip()
            time_arr = cur_time.split()
            if time_arr[2] == 'PM':
                hms = time_arr[1].split(':')
                hms[0] = str(int(hms[0]) + 12)
                datalogger_start_time = ':'.join(hms)
            else:
                datalogger_start_time = time_arr[2]
            datalogger_start_time_seconds = time2seconds(
                datalogger_start_time)
        elif line_num > 3:
            break

datalogger_lastrow = get_last_row(datalogger_input_path)
datalogger_end_time_seconds = datalogger_start_time_seconds + float(
    datalogger_lastrow[0])

# Bioharness file #############################################################
bioharness_output_path = './output/synced_' + bioharness_input_path[2:]
with open(bioharness_input_path, 'r') as f:
    lastrow = None
    firstrow = None
    for line_num, row in enumerate(csv.reader(f), 1):
        if line_num == 2:
            firstrow = row
        else:
            pass
    lastrow = row
bioharness_start_time = firstrow[0].split()[1].split('.')[0]
bioharness_start_time_seconds = time2seconds(bioharness_start_time)
bioharness_end_time = lastrow[0].split()[1].split('.')[0]
bioharness_end_time_seconds = time2seconds(bioharness_end_time)

# Decide the time period!!! ###################################################
start_time = max(video_start_time_seconds, datalogger_start_time_seconds,
                 bioharness_start_time_seconds)
end_time = min(video_end_time_seconds, datalogger_end_time_seconds,
               bioharness_end_time_seconds)
duration = end_time - start_time

delta_time_datalogger = start_time - datalogger_start_time_seconds
delta_time_bioharness = start_time - bioharness_start_time_seconds

def datalogger_sync():
    # ========================= Datalogger Sync Start ========================
    with open(datalogger_input_path, 'r') as inp, open(
            datalogger_output_path, 'w', newline='') as out:
        writer = csv.writer(out)

        for line_num, row in enumerate(csv.reader(inp), 1):
            # retrieve the datalogger start time and convert to seconds
            if line_num == 3:
                # update the datalogger start time
                row[0] = ' '.join(
                    [row[0][:idx + 1], time_arr[0], video_start_time])
                writer.writerow(row)

            elif line_num <= 6:
                # write headers
                writer.writerow(row)
            else:
                # write data with (time - delta_v_d > 0)
                relative_time = float(row[0]) - delta_time_datalogger
                if relative_time >= 0 and relative_time <= duration:
                    # print current time to check status
                    if relative_time.is_integer():
                        print("Datalogger row: " + str(relative_time))
                    relative_time = Decimal(relative_time)
                    relative_time = round(relative_time, 2)
                    row[0] = str(relative_time)
                    writer.writerow(row)

    print("Successfully sync datalogger data!!!")
    # ========================= Datalogger Sync end ===========================

def bioharness_sync():
    # ======================= Bioharness Sync start ===========================
    with open(bioharness_input_path, 'r') as inp, open(
            bioharness_output_path, 'w', newline='') as out:
        writer = csv.writer(out)

        for line_num, row in enumerate(csv.reader(inp), -1):
            if line_num == -1:
                # write headers
                writer.writerow(row)
            elif line_num >= delta_time_bioharness and line_num - delta_time_bioharness <= duration:
                print("Bioharness row: " + str(line_num + 2))
                writer.writerow(row)

    print("Successfully sync bioharness data!!!")

    # ======================== Bioharness Sync end ============================

def video_clip():
    # ========================= Video Clip start ==============================
    imageio.plugins.ffmpeg.download()
    from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

    video_list = os.listdir(video_path)
    for name in video_list:
        input_path = video_path + '/' + name
        output_path = './output/synced_' + name
        ffmpeg_extract_subclip(input_path, 0, duration, targetname=output_path)

    print("Video Clip Successfully!!!")
    # ========================= Video Clip end ===========================

def main():
    datalogger_sync()
    bioharness_sync()
    video_clip()

if __name__ == '__main__':
    main()
