# Internet Checker

Internet Checker is a Python script that helps you monitor and report on your internet connection. It performs periodic speed tests, tracks connectivity status, and generates daily, weekly, and monthly reports with modern, minimalistic graphs.

## Features

- Automated internet speed tests
- Continuous monitoring of connectivity status
- Daily, weekly, and monthly reports
- Modern and minimalistic line graphs
- Integration with Telegram for report delivery

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.x installed
- Required Python libraries (install using `pip`):
  - `speedtest-cli`
  - `matplotlib`
  - `seaborn`
  - `requests`
  - `python-telegram-bot`

## Getting Started

1. Clone this repository:

   ```shell
   git clone https://github.com/Rishi16/internet-checker.git
   ```

2. Install the required libraries:

   ```shell
   pip install -r requirements.txt
   ```

3. Create a `_secrets.py` file and add your Telegram Bot Token and Chat ID:

   ```python
   TELEGRAM_BOT_TOKEN = "your_bot_token"
   CHAT_ID = "your_chat_id"
   ABS_PATH = "path_to_project_root"
   ```

4. Run the script:

   ```shell
   python internet_checker.py
   ```

## Usage

- The script will continuously monitor your internet connectivity and perform hourly speed tests.
- Daily reports are sent at 9 PM (configurable) and include daily speed test results and downtime information.
- Weekly reports are sent on Sundays (configurable) and provide a summary of the week's data.
- Monthly reports are sent on the last day of the month (configurable) and include monthly statistics.

### Manual Report Generation

You can manually generate reports using command-line arguments. Use the following options:

- `-d` or `--daily`: Generate and send a daily report.
- `-w` or `--weekly`: Generate and send a weekly report.
- `-m` or `--monthly`: Generate and send a monthly report.

Example:

```shell
python internet_checker.py -d  # Generate and send a daily report
```

## Customization

You can customize the script by modifying the following settings in `internet_checker.py`:

- Report delivery timing (daily, weekly, monthly)
- Report file names and formats
- Report content (e.g., add or remove specific statistics)
- Graph styling (e.g., colors, labels)

## Acknowledgments

- [Speedtest by Ookla](https://www.speedtest.net/) for the speed test functionality.
- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/en/stable/) for Telegram integration.
- [Matplotlib](https://matplotlib.org/) and [Seaborn](https://seaborn.pydata.org/) for data visualization.

## Contributing

Contributions are welcome! Feel free to open an issue or pull request to improve this project.

