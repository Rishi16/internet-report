import os
import time
import datetime
from math import floor

import speedtest
import requests
import json
from telegram import Bot
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from _secrets import TELEGRAM_BOT_TOKEN, CHAT_ID
import asyncio
import seaborn as sns
from statistics import median, mode, StatisticsError


TS = "%Y-%m-%d %H:%M:%S"

# Define the report and data directory paths
ABS_PATH = os.path.abspath(".")
REPORT_DIRECTORY = os.path.join(ABS_PATH, "reports")
DATA_DIRECTORY = os.path.join(ABS_PATH, "data")
print(REPORT_DIRECTORY, DATA_DIRECTORY)
bot = Bot(token=TELEGRAM_BOT_TOKEN)


# Function to ensure the directory exists
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def setup():
    month = datetime.datetime.now().strftime("%Y-%m")
    connectivity_file = os.path.join(DATA_DIRECTORY, f"connectivity_{month}.json")
    speedtest_file = os.path.join(DATA_DIRECTORY, f"speedtest_{month}.json")
    # Ensure the report and data directories exist
    ensure_directory_exists(REPORT_DIRECTORY)
    ensure_directory_exists(DATA_DIRECTORY)

    if not os.path.exists(connectivity_file):
        with open(connectivity_file, "w") as f:
            json.dump([], f)
    if not os.path.exists(speedtest_file):
        with open(speedtest_file, "w") as f:
            json.dump([], f)

    # Check connectivity every minute
    with open(connectivity_file, "r") as f:
        connectivity_data = json.load(f)
    # Check connectivity every minute
    with open(speedtest_file, "r") as f:
        speed_data = json.load(f)

    return connectivity_data, speed_data


def calculate_stats(data):
    median_value = median(data)
    try:
        mode_value = mode(data)
    except StatisticsError:
        mode_value = data[0]
    return median_value, mode_value


def format_minutes_as_time(minutes):
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    elif minutes < 1440:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours} hour{'s' if hours > 1 else ''} and {remaining_minutes} minute{'s' if remaining_minutes > 1 else ''}"
    else:
        days = minutes // 1440
        remaining_minutes = minutes % 1440
        hours = remaining_minutes // 60
        remaining_minutes %= 60
        time_str = f"{days} day{'s' if days > 1 else ''}"
        if hours > 0:
            time_str += f", {hours} hour{'s' if hours > 1 else ''}"
        if remaining_minutes > 0:
            time_str += (
                f", {remaining_minutes} minute{'s' if remaining_minutes > 1 else ''}"
            )
        return time_str


# Function to check internet connectivity
def check_connectivity():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False


# Function to run speed test
def run_speed_test():
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = round(st.download() / 1024 / 1024, 2)  # Convert to Mbps
    upload_speed = round(st.upload() / 1024 / 1024, 2)  # Convert to Mbps
    return download_speed, upload_speed


# Function to create a modern and minimalistic line graph
def create_line_graph(x, y, title, xlabel, ylabel, filename, report_type):
    filepath = os.path.join(REPORT_DIRECTORY, filename)

    sns.set(style="whitegrid")  # Set seaborn style for better styling

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(
        x, y, marker="o", markersize=6, linestyle="-", linewidth=2, color="#007acc"
    )  # Adjust line style and color
    ax.set_title(title, fontsize=16)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

    if report_type == "daily":
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    elif report_type in ["weekly", "monthly"]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m"))

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filepath, bbox_inches="tight")  # Ensure tight bounding box for saving
    plt.close()
    return filepath


# Function to send a message with an optional image to Telegram
async def send_telegram_photo(image_path=None):
    image_path = os.path.join(REPORT_DIRECTORY, image_path)
    if image_path:
        with open(image_path, "rb") as img:
            await bot.send_photo(chat_id=CHAT_ID, photo=img)


# Function to send a message with an optional image to Telegram
async def send_telegram_message(message):
    await bot.send_message(chat_id=CHAT_ID, text=message)


# Function to send daily report
async def send_daily_report(speed_data, connectivity_data):
    # Calculate uptime and downtime for the day
    today = datetime.date.today().strftime("%Y-%m-%d")
    today_connectivity_data = [
        entry["status"]
        for entry in connectivity_data
        if entry["time"].startswith(today)
    ]

    total_downtime = format_minutes_as_time(today_connectivity_data.count(0))
    total_uptime = format_minutes_as_time(today_connectivity_data.count(1))

    # Calculate average daily speed
    today_speed_data = [
        entry for entry in speed_data if entry["time"].startswith(today)
    ]
    avg_download_speed = sum(
        [entry["download_speed"] for entry in today_speed_data]
    ) / len(today_speed_data)
    avg_upload_speed = sum([entry["upload_speed"] for entry in today_speed_data]) / len(
        today_speed_data
    )

    # Calculate median and mode of download and upload speeds
    download_speeds = [entry["download_speed"] for entry in today_speed_data]
    upload_speeds = [entry["upload_speed"] for entry in today_speed_data]
    median_download, mode_download = calculate_stats(download_speeds)
    median_upload, mode_upload = calculate_stats(upload_speeds)

    # Create and save a minimalistic line graph for hourly speed on the day
    timestamps = [
        datetime.datetime.strptime(entry["time"], TS) for entry in today_speed_data
    ]
    download_speeds = [entry["download_speed"] for entry in today_speed_data]
    upload_speeds = [entry["upload_speed"] for entry in today_speed_data]
    create_line_graph(
        timestamps,
        download_speeds,
        "Daily Speed Test Results",
        "Hour",
        "Download Speed (Mbps)",
        "daily_download_speed_graph.png",
        "daily",
    )
    create_line_graph(
        timestamps,
        upload_speeds,
        "Daily Speed Test Results",
        "Hour",
        "Upload Speed (Mbps)",
        "daily_upload_speed_graph.png",
        "daily",
    )

    # Send the daily report with the minimalistic graphs
    message = f"Daily Report - {today}\n"
    message += f"Total Uptime: {total_uptime} hours\n"
    message += f"Total Downtime: {total_downtime} hours\n"
    message += f"Average Download Speed: {avg_download_speed:.2f} Mbps\n"
    message += f"Average Upload Speed: {avg_upload_speed:.2f} Mbps\n"
    message += f"Median Download Speed: {median_download:.2f} Mbps\n"
    message += f"Mode Download Speed: {mode_download:.2f} Mbps\n"
    message += f"Median Upload Speed: {median_upload:.2f} Mbps\n"
    message += f"Mode Upload Speed: {mode_upload:.2f} Mbps\n"

    await send_telegram_message(message)
    await send_telegram_photo("daily_download_speed_graph.png")
    await send_telegram_photo("daily_upload_speed_graph.png")


# Function to send weekly report
async def send_weekly_report(speed_data, connectivity_data):
    # Calculate total downtime in terms of days for the week
    current_date = datetime.date.today()
    start_of_week = current_date - datetime.timedelta(days=current_date.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    week_connectivity_data = [
        entry["status"]
        for entry in connectivity_data
        if start_of_week
        <= datetime.datetime.strptime(entry["time"], TS).date()
        <= end_of_week
    ]

    total_downtime_days = format_minutes_as_time(week_connectivity_data.count(0))

    # Calculate average weekly speed
    week_speed_data = [
        entry
        for entry in speed_data
        if start_of_week
        <= datetime.datetime.strptime(entry["time"], TS).date()
        <= end_of_week
    ]
    avg_download_speed = sum(
        [entry["download_speed"] for entry in week_speed_data]
    ) / len(week_speed_data)
    avg_upload_speed = sum([entry["upload_speed"] for entry in week_speed_data]) / len(
        week_speed_data
    )
    download_speeds = [entry["download_speed"] for entry in week_speed_data]
    upload_speeds = [entry["upload_speed"] for entry in week_speed_data]
    median_download, mode_download = calculate_stats(download_speeds)
    median_upload, mode_upload = calculate_stats(upload_speeds)

    # Create and save a minimalistic line graph for the week's speed test results
    timestamps = [
        datetime.datetime.strptime(entry["time"], TS) for entry in week_speed_data
    ]
    download_speeds = [entry["download_speed"] for entry in week_speed_data]
    upload_speeds = [entry["upload_speed"] for entry in week_speed_data]
    create_line_graph(
        timestamps,
        download_speeds,
        "Weekly Speed Test Results",
        "Date",
        "Download Speed (Mbps)",
        "weekly_download_speed_graph.png",
        "weekly",
    )
    create_line_graph(
        timestamps,
        upload_speeds,
        "Weekly Speed Test Results",
        "Date",
        "Upload Speed (Mbps)",
        "weekly_upload_speed_graph.png",
        "weekly",
    )

    # Send the weekly report with the minimalistic graphs
    message = "-" * 30
    message += f"\nWeekly Report - {start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}\n"
    message += f"Total Downtime (Days): {total_downtime_days}\n"
    message += f"Average Download Speed: {avg_download_speed:.2f} Mbps\n"
    message += f"Average Upload Speed: {avg_upload_speed:.2f} Mbps\n"
    message += f"Median Download Speed: {median_download:.2f} Mbps\n"
    message += f"Mode Download Speed: {mode_download:.2f} Mbps\n"
    message += f"Median Upload Speed: {median_upload:.2f} Mbps\n"
    message += f"Mode Upload Speed: {mode_upload:.2f} Mbps\n"

    await send_telegram_message(message)
    await send_telegram_photo("weekly_download_speed_graph.png")
    await send_telegram_photo("weekly_upload_speed_graph.png")


# Function to generate and send the monthly report
async def send_monthly_report(speed_data, connectivity_data):
    # Calculate total downtime in terms of days and hours for the month
    month_connectivity_data = [entry["status"] for entry in connectivity_data]
    total_downtime_days = format_minutes_as_time(month_connectivity_data.count(0))

    # Calculate average monthly speed
    avg_download_speed = sum([entry["download_speed"] for entry in speed_data]) / len(
        speed_data
    )
    avg_upload_speed = sum([entry["upload_speed"] for entry in speed_data]) / len(
        speed_data
    )

    # Create and save a minimalistic line graph for the month's speed test results
    timestamps = [datetime.datetime.strptime(entry["time"], TS) for entry in speed_data]
    download_speeds = [entry["download_speed"] for entry in speed_data]
    upload_speeds = [entry["upload_speed"] for entry in speed_data]
    median_download, mode_download = calculate_stats(download_speeds)
    median_upload, mode_upload = calculate_stats(upload_speeds)

    create_line_graph(
        timestamps,
        download_speeds,
        "Monthly Speed Test Results",
        "Date",
        "Download Speed (Mbps)",
        "monthly_download_speed_graph.png",
        "monthly",
    )
    create_line_graph(
        timestamps,
        upload_speeds,
        "Monthly Speed Test Results",
        "Date",
        "Upload Speed (Mbps)",
        "monthly_upload_speed_graph.png",
        "monthly",
    )

    # Send the monthly report with the minimalistic graphs
    message = "*" * 30
    message += f"\nMonthly Report - {datetime.datetime.now().strftime('%B %Y')}\n"
    message += f"Total Downtime (Days): {total_downtime_days}\n"
    message += f"Average Download Speed: {avg_download_speed:.2f} Mbps\n"
    message += f"Average Upload Speed: {avg_upload_speed:.2f} Mbps\n"
    message += f"Median Download Speed: {median_download:.2f} Mbps\n"
    message += f"Mode Download Speed: {mode_download:.2f} Mbps\n"
    message += f"Median Upload Speed: {median_upload:.2f} Mbps\n"
    message += f"Mode Upload Speed: {mode_upload:.2f} Mbps\n"

    await send_telegram_message(message)
    await send_telegram_photo("monthly_download_speed_graph.png")
    await send_telegram_photo("monthly_upload_speed_graph.png")
    await send_telegram_message("*" * 30)


# Main function
async def main():
    internet_is_up = True
    hourly_pending = daily_pending = weekly_pending = monthly_pending = False
    down_time = datetime.datetime.now()

    connectivity_data, speed_data = setup()
    while True:
        month = datetime.datetime.now().strftime("%Y-%m")
        connectivity_file = os.path.join(DATA_DIRECTORY, f"connectivity_{month}.json")
        speedtest_file = os.path.join(DATA_DIRECTORY, f"speedtest_{month}.json")

        if check_connectivity():
            status = 1
            if not internet_is_up:
                internet_is_up = True
                down = format_minutes_as_time(
                    floor((datetime.datetime.now() - down_time).total_seconds() / 60)
                )
                message = f"Internet is UP!\nDowntime: {down}"
                await send_telegram_message(message)
        else:
            status = 0
            if internet_is_up:
                internet_is_up = False
                down_time = datetime.datetime.now()
        connectivity_data.append(
            {
                "status": status,
                "time": datetime.datetime.now().strftime(TS),
            }
        )
        with open(connectivity_file, "w") as f:
            json.dump(connectivity_data, f)

        # Check if it's the top of the hour (hourly speed check)
        if datetime.datetime.now().minute == 0 or hourly_pending:
            if internet_is_up:
                hourly_pending = False
                download_speed, upload_speed = run_speed_test()
                with open(speedtest_file, "r") as f:
                    speed_data = json.load(f)
                speed_data.append(
                    {
                        "download_speed": download_speed,
                        "upload_speed": upload_speed,
                        "time": datetime.datetime.now().strftime(TS),
                    }
                )
                with open(speedtest_file, "w") as f:
                    json.dump(speed_data, f)
            else:
                hourly_pending = True

        # Check if it's 9 PM to send the daily report
        if (
            datetime.datetime.now().hour == 21 and datetime.datetime.now().minute == 0
        ) or daily_pending:
            if internet_is_up:
                daily_pending = False
                await send_daily_report(speed_data, connectivity_data)
            else:
                daily_pending = True

        # Check if it's Sunday to send the weekly report
        if (
            datetime.datetime.now().weekday() == 6
            and datetime.datetime.now().hour == 21
            and datetime.datetime.now().minute == 0
        ) or weekly_pending:
            if internet_is_up:
                weekly_pending = False
                await send_weekly_report(speed_data, connectivity_data)
            else:
                weekly_pending = True

        # Check if it's the last day of the month to send the monthly report
        last_day_of_month = (
            datetime.datetime.now().replace(day=1) + datetime.timedelta(days=32)
        ).replace(day=1) - datetime.timedelta(days=1)
        if (
            datetime.datetime.now().date() == last_day_of_month.date()
            and datetime.datetime.now().hour == 21
            and datetime.datetime.now().minute == 0
        ) or monthly_pending:
            if internet_is_up:
                monthly_pending = False
                await send_monthly_report(speed_data, connectivity_data)
            else:
                monthly_pending = True
        # Sleep for 1 minute
        time.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
