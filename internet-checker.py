import os
import time
import datetime
import speedtest
import requests
import json
from telegram import Bot
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Telegram bot API token
TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN'
# Your chat ID, you can find this out by messaging the bot and checking the updates
CHAT_ID = 'YOUR_CHAT_ID'
# Cost of your internet plan per month (Rupees)
INTERNET_COST = 1050
# Your internet plan speed (Mbps)
INTERNET_SPEED = 100

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
    download_speed = st.download() / 1024 / 1024  # Convert to Mbps
    upload_speed = st.upload() / 1024 / 1024  # Convert to Mbps
    return download_speed, upload_speed

# Function to send a message with an optional image to Telegram
def send_telegram_message(message, image_path=None):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)
    if image_path:
        with open(image_path, 'rb') as img:
            bot.send_photo(chat_id=CHAT_ID, photo=img)

# Function to create a minimalistic line graph
def create_line_graph(x, y, title, xlabel, ylabel, filename):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, y, marker='o', linestyle='-')
    ax.set_title(title, fontsize=16)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# Function to send daily report
def send_daily_report(speed_data, connectivity_data):
    # Calculate uptime and downtime for the day
    today = datetime.date.today().strftime('%Y-%m-%d')
    today_connectivity_data = [entry['status'] for entry in connectivity_data if entry['time'].startswith(today)]

    total_uptime = sum(today_connectivity_data)
    total_downtime = 24 - total_uptime

    # Calculate average daily speed
    today_speed_data = [entry for entry in speed_data if entry['time'].startswith(today)]
    avg_download_speed = sum([entry['download_speed'] for entry in today_speed_data]) / len(today_speed_data)
    avg_upload_speed = sum([entry['upload_speed'] for entry in today_speed_data]) / len(today_speed_data)

    # Create and save a minimalistic line graph for hourly speed on the day
    timestamps = [datetime.datetime.strptime(entry['time'], '%Y-%m-%d %H:%M:%S') for entry in today_speed_data]
    download_speeds = [entry['download_speed'] for entry in today_speed_data]
    upload_speeds = [entry['upload_speed'] for entry in today_speed_data]
    create_line_graph(timestamps, download_speeds, 'Daily Speed Test Results', 'Hour', 'Download Speed (Mbps)', 'daily_speed_graph.png')
    create_line_graph(timestamps, upload_speeds, 'Daily Speed Test Results', 'Hour', 'Upload Speed (Mbps)', 'daily_upload_speed_graph.png')

    # Send the daily report with the minimalistic graphs
    message = f"Daily Report - {today}\n"
    message += f"Total Uptime: {total_uptime} hours\n"
    message += f"Total Downtime: {total_downtime} hours\n"
    message += f"Average Download Speed: {avg_download_speed:.2f} Mbps\n"
    message += f"Average Upload Speed: {avg_upload_speed:.2f} Mbps"

    send_telegram_message(message, image_path='daily_speed_graph.png')
    send_telegram_message(message, image_path='daily_upload_speed_graph.png')

# Function to send weekly report
def send_weekly_report(speed_data, connectivity_data):
    # Calculate total downtime in terms of days for the week
    current_date = datetime.date.today()
    start_of_week = current_date - datetime.timedelta(days=current_date.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    week_connectivity_data = [entry['status'] for entry in connectivity_data if start_of_week <= datetime.datetime.strptime(entry['time'], '%Y-%m-%d %H:%M:%S').date() <= end_of_week]

    total_downtime_days = (7 - sum(week_connectivity_data)) / 24

    # Calculate average weekly speed
    week_speed_data = [entry for entry in speed_data if start_of_week <= datetime.datetime.strptime(entry['time'], '%Y-%m-%d %H:%M:%S').date() <= end_of_week]
    avg_download_speed = sum([entry['download_speed'] for entry in week_speed_data]) / len(week_speed_data)
    avg_upload_speed = sum([entry['upload_speed'] for entry in week_speed_data]) / len(week_speed_data)

    # Create and save a minimalistic line graph for the week's speed test results
    timestamps = [datetime.datetime.strptime(entry['time'], '%Y-%m-%d %H:%M:%S') for entry in week_speed_data]
    download_speeds = [entry['download_speed'] for entry in week_speed_data]
    upload_speeds = [entry['upload_speed'] for entry in week_speed_data]
    create_line_graph(timestamps, download_speeds, 'Weekly Speed Test Results', 'Date', 'Download Speed (Mbps)', 'weekly_speed_graph.png')
    create_line_graph(timestamps, upload_speeds, 'Weekly Speed Test Results', 'Date', 'Upload Speed (Mbps)', 'weekly_upload_speed_graph.png')

    # Send the weekly report with the minimalistic graphs
    message = f"Weekly Report - {start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}\n"
    message += f"Total Downtime (Days): {total_downtime_days:.2f}\n"
    message += f"Average Download Speed: {avg_download_speed:.2f} Mbps\n"
    message += f"Average Upload Speed: {avg_upload_speed:.2f} Mbps"

    send_telegram_message(message, image_path='weekly_speed_graph.png')
    send_telegram_message(message, image_path='weekly_upload_speed_graph.png')

# Function to generate and send the monthly report
def send_monthly_report(speed_data, connectivity_data):
    # Calculate total downtime in terms of days and hours for the month
    total_downtime_hours = 24 * (datetime.datetime.now().day - 1) + (24 - sum(connectivity_data))
    total_downtime_days = total_downtime_hours / 24

    # Calculate average monthly speed
    avg_download_speed = sum([entry['download_speed'] for entry in speed_data]) / len(speed_data)
    avg_upload_speed = sum([entry['upload_speed'] for entry in speed_data]) / len(speed_data)

    # Create and save a minimalistic line graph for the month's speed test results
    timestamps = [datetime.datetime.strptime(entry['time'], '%Y-%m-%d %H:%M:%S') for entry in speed_data]
    download_speeds = [entry['download_speed'] for entry in speed_data]
    upload_speeds = [entry['upload_speed'] for entry in speed_data]
    create_line_graph(timestamps, download_speeds, 'Monthly Speed Test Results', 'Date', 'Download Speed (Mbps)', 'monthly_speed_graph.png')
    create_line_graph(timestamps, upload_speeds, 'Monthly Speed Test Results', 'Date', 'Upload Speed (Mbps)', 'monthly_upload_speed_graph.png')

    # Send the monthly report with the minimalistic graphs
    message = f"Monthly Report - {datetime.datetime.now().strftime('%B %Y')}\n"
    message += f"Total Downtime (Days): {total_downtime_days:.2f}\n"
    message += f"Average Download Speed: {avg_download_speed:.2f} Mbps\n"
    message += f"Average Upload Speed: {avg_upload_speed:.2f} Mbps"

    send_telegram_message(message, image_path='monthly_speed_graph.png')
    send_telegram_message(message, image_path='monthly_upload_speed_graph.png')


# Main function
if __name__ == "__main__":
    current_month = datetime.datetime.now().strftime('%Y-%m')
    connectivity_file = f'connectivity_{current_month}.json'
    speedtest_file = f'speedtest_{current_month}.json'

    while True:
        # Check if it's a new month and create new data files
        new_month = datetime.datetime.now().strftime('%Y-%m')
        if new_month != current_month:
            connectivity_file = f'connectivity_{new_month}.json'
            speedtest_file = f'speedtest_{new_month}.json'
            current_month = new_month

        # Check connectivity every minute
        with open(connectivity_file, 'r') as f:
            connectivity_data = json.load(f)
        connectivity_data.append({
            'status': 1 if check_connectivity() else 0,
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        with open(connectivity_file, 'w') as f:
            json.dump(connectivity_data, f)

        # Check if it's the top of the hour (hourly speed check)
        if datetime.datetime.now().minute == 0:
            download_speed, upload_speed = run_speed_test()
            with open(speedtest_file, 'r') as f:
                speed_data = json.load(f)
            speed_data.append({
                'download_speed': download_speed,
                'upload_speed': upload_speed,
                'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            with open(speedtest_file, 'w') as f:
                json.dump(speed_data, f)

        # Check if it's 9 PM to send the daily report
        if datetime.datetime.now().hour == 21 and datetime.datetime.now().minute == 0:
            send_daily_report(speed_data, connectivity_data)

        # Check if it's Sunday to send the weekly report
        if datetime.datetime.now().weekday() == 6 and datetime.datetime.now().hour == 0 and datetime.datetime.now().minute == 0:
            send_weekly_report()

        # Check if it's the last day of the month to send the monthly report
        last_day_of_month = (datetime.datetime.now().replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
        if datetime.datetime.now().date() == last_day_of_month.date() and datetime.datetime.now().hour == 0 and datetime.datetime.now().minute == 0:
            send_monthly_report(speed_data, connectivity_data)

        # Sleep for 1 minute
        time.sleep(60)
