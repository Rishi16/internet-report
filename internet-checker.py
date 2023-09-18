import os
import time
import datetime
import speedtest
import requests
import json
from telegram import Bot

# Telegram bot API token
TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN'
# Your chat ID, you can find this out by messaging the bot and checking the updates
CHAT_ID = 'YOUR_CHAT_ID'

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

# Function to send hourly speed report for today's data
def send_hourly_speed_report(speed_data):
    today = datetime.date.today().strftime('%Y-%m-%d')
    today_speed_data = [entry for entry in speed_data if entry['time'].startswith(today)]

    if today_speed_data:
        max_speed = max(today_speed_data, key=lambda x: x['download_speed'])
        avg_download_speed = sum([x['download_speed'] for x in today_speed_data]) / len(today_speed_data)
        avg_upload_speed = sum([x['upload_speed'] for x in today_speed_data]) / len(today_speed_data)
        message = f"Hourly Speed Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"Max Download Speed: {max_speed['download_speed']:.2f} Mbps (at {max_speed['time']})\n"
        message += f"Avg Download Speed: {avg_download_speed:.2f} Mbps\n"
        message += f"Avg Upload Speed: {avg_upload_speed:.2f} Mbps"
        send_telegram_message(message)

# Function to send daily connectivity report for today's data
def send_daily_connectivity_report(connectivity_data):
    today = datetime.date.today().strftime('%Y-%m-%d')
    today_connectivity_data = [entry['status'] for entry in connectivity_data if entry['time'].startswith(today)]

    total_uptime = sum(today_connectivity_data)
    total_downtime = 24 - total_uptime
    message = f"Daily Connectivity Report - {datetime.datetime.now().strftime('%Y-%m-%d')}\n"
    message += f"Total Uptime: {total_uptime} hours\n"
    message += f"Total Downtime: {total_downtime} hours"
    send_telegram_message(message)

# Function to send combined daily report for today's data
def send_daily_report(speed_data, connectivity_data):
    send_hourly_speed_report(speed_data)
    send_daily_connectivity_report(connectivity_data)

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
            send_monthly_report()

        # Sleep for 1 minute
        time.sleep(60)
