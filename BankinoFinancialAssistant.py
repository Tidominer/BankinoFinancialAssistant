import pandas as pd
import matplotlib.pyplot as plt
import datetime
import jalali_pandas
import sys
import warnings
import argparse


def persian_to_english_digits(text):
    # Create a translation map for Persian digits to English digits
    translation_table = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    return text.translate(translation_table)
    
def draw_ascii_graph(data, title, y_label, height):
    result = ""

    max_value = max(data)
    min_value = min(data)
    range_value = max_value - min_value
    #height = 10  # Height of the graph in rows
    scale = height / range_value if range_value > 0 else 1

    result += f"\n{title}"
    result += f" {y_label} (Max: {max_value:,}, Min: {min_value:,})\n"
    result += "+" + "-" * 40 + "+" + "\n"
    
    for i in range(height, -1, -1):
        line = f"{min_value + (i / scale):12,.0f} |"
        for value in data:
            # Calculate row position
            pos = round((value - min_value) * scale)
            if pos == i and pos != 0:
                line += "▄"
            else:
                if (pos < i):
                    line += " "
                elif (pos == 0):
                    line += "‗";
                else:
                    line += "█"
        result += line + "\n"
    result += "+" + "-" * 40 + "+" + "\n"
    result += " " * 14 + "".join(["|"] * len(data)) + "\n"
    return result;

def print_title(title):
    print()
    print("╔"+ ("═"*(6+len(title))) + "╗")
    print("║" + " "*3 + title + " "*3 + "║")
    print("╚"+ ("═"*(6+len(title))) + "╝")
    print()

def valid_date(s: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a Valid Date: {s!r}")

print_title("Bankino Financial Assistant v0.2");

parser = argparse.ArgumentParser(
                    prog='Bankino Financial Assistant',
                    description='This script analyzes Bankino\'s exported transactions excel file and provides a report of your total income, cost and balance and plots these data over a timeline in the terminal environment',
                    epilog='visit https://wwww.github.com/Tidominer/BankinoFinancialAssistant if you need more informaiton about this tool.')

parser.add_argument('filename', type=str, help="Name or address to the excel data file")
parser.add_argument('-s', '--start', type=valid_date, help="Start date of the data to take (YYYY-MM-DD)")
parser.add_argument('-e', '--end', type=valid_date, help="End date of the data to take (YYYY-MM-DD)")
parser.add_argument('-g', '--height', type=int, help="Height of the drawn graphs")
parser.add_argument('-o', '--output', type=str, help="Name or address of the file to export the data.")

args = parser.parse_args()

# Load the Excel file
file_path = args.filename

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    df = pd.read_excel(file_path)


# Rename columns for easier handling
df.columns = ['Date', 'Time', 'Amount', 'Balance', 'Type', 'Title', 'Description']

# Convert the Persian date to a proper datetime format (assuming the Persian calendar is in use)
df['Date'] = df['Date'].apply(persian_to_english_digits).jalali.parse_jalali("%Y-%m-%d").jalali.to_gregorian()

# Filter for the past n days

if args.height is not None:
    height = args.height
else:
    height = 10

if args.start is not None:
    df_filtered = df[df['Date'] >= args.start]
else:
    df_filtered = df;

if args.end is not None:
    df_filtered = df_filtered[df_filtered['Date'] <= args.end]

if not df_filtered.empty:
    # Reset the index to make indexing sequential
    df_filtered = df_filtered.reset_index(drop=False)

    # Calculate the absolute number of days between the first and last date
    days = abs((df_filtered['Date'][0] - df_filtered['Date'][len(df_filtered) - 1]).days)+1
else:
    days = 0

# Calculate total income and costs
total_income = df_filtered[df_filtered['Type'] == 'واریز']['Amount'].sum()
total_costs = df_filtered[df_filtered['Type'] == 'برداشت']['Amount'].sum()

date_range = pd.date_range(df_filtered['Date'].min(), df_filtered['Date'].max(), freq='D')

# Handle duplicate dates by aggregating with sum for income and costs
income_data = (
    df_filtered[df_filtered['Type'] == 'واریز']
    .groupby('Date')['Amount'].sum()  # Aggregate duplicate dates by summing
    .reindex(date_range, fill_value=0)  # Align to date_range, fill missing values with 0
    .tolist()
)

costs_data = (
    df_filtered[df_filtered['Type'] == 'برداشت']
    .groupby('Date')['Amount'].sum()  # Aggregate duplicate dates by summing
    .reindex(date_range, fill_value=0)  # Align to date_range, fill missing values with 0
    .tolist()
)

# Handle duplicates for balance by taking the last value for each date
balance_data = (
    df_filtered.groupby('Date')['Balance'].last()  # Use the last available balance for each date
    .reindex(date_range, method='ffill')  # Align to date_range, forward-fill missing values
    .fillna(0)  # Fill any leading NaNs with 0
    .tolist()
)

output = ""

print(f"{len(df_filtered)} rows analyzed from {df_filtered['Date'][0].date()} to {df_filtered['Date'][len(df_filtered) - 1].date()}")
output += f"{len(df_filtered)} rows analyzed from {df_filtered['Date'][0].date()} to {df_filtered['Date'][len(df_filtered) - 1].date()}" + "\n"

# Draw ASCII graphs
income_graph = draw_ascii_graph(income_data, f"Income in {days} Days", "Incoming Transactions", height)
output += income_graph + "\n"
print(income_graph)

costs_graph = draw_ascii_graph(costs_data, f"Costs in {days} Days", "Outgoing Transactions", height)
output += costs_graph + "\n"
print(costs_graph)

balance_graph = draw_ascii_graph(balance_data, f"Balance in {days} Days", "Balance", height)
output += balance_graph + "\n\n"
print(balance_graph)

print()

# Print summary
print(f"Summary of Transactions in the Past {days} Days:")
output += (f"Summary of Transactions in the Past {days} Days:") + "\n"

print(f"Total Income: {total_income:,} Rial")
output += (f"Total Income: {total_income:,} Rial") + "\n"

print(f"Total Costs: {total_costs:,} Rial")
output += (f"Total Costs: {total_costs:,} Rial") + "\n"

if (args.output is not None):
    f = open(args.output, "w", encoding='utf-8')
    f.write(output)
    f.close()