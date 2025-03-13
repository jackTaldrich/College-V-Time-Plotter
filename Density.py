import csv
from datetime import datetime

acceptance_rate = "Acceptance Rate"
date_column = "Date"
values = []
cap = 35

def convert_date(date_str):
    """Converts a date from 'DD-MMM-YYYY' to 'YYYY-MM-DD HH:MM:SS'."""
    try:
        date_obj = datetime.strptime(date_str, "%d-%b-%Y")
        return date_obj
    except ValueError:
        return None


start = convert_date(input("Starting date? (01-Oct-2024)\n :") or "01-Oct-2024")
end = convert_date(input("Ending date? (01-Jan-2025)\n :") or "01-Jan-2025")

if start is None or end is None:
    print("Invalid date format entered. Please use 'DD-MMM-YYYY'.")
    exit()

try:
    cap = int(input("What is the max acceptance rate allowed? (35)\n :") or 35)

    if cap < 0 or cap > 100:
        print("Invalid acceptance rate entered. Please use '0-100'.")
        exit()
except ValueError:
    print("Invalid acceptance rate entered. Please use '0-100'.")
    exit()

date_range = (end - start).days + 1
filtered_count = 0

with open("college_emails.csv", mode="r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        row_date = datetime.strptime(row[date_column], "%Y-%m-%d %H:%M:%S")

        if start <= row_date <= end:
            if int(row[acceptance_rate]) <= cap:
                filtered_count += 1

density = filtered_count / date_range if date_range is not None else 0

print(f"Total filtered emails: {filtered_count}")
print(f"Date range (days): {date_range}")
print(f"Density of low acceptance rates: {density:.4f} emails/day")
