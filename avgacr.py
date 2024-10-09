import csv
import datetime
from collections import defaultdict

# Dictionary to store the acceptance rates for each day
acceptance_rates_by_day = defaultdict(list)

with open('college_emails.csv', mode='r', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    # Skip the header
    next(reader)

    for row in reader:
        date_str = row[0]
        acceptance_rate = float(row[2])

        # Convert the date string to a datetime object and extract only the date part
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()

        # Append the acceptance rate to the list for this particular date
        acceptance_rates_by_day[date].append(acceptance_rate)

# Calculate the average acceptance rate for each day
average_acceptance_by_day = {
    date: sum(rates) / len(rates) for date, rates in acceptance_rates_by_day.items()
}

# # Print the results
# for date, avg_rate in average_acceptance_by_day.items():
#     print(f"{date}: {avg_rate:.2f}%")

with open('avgacr.csv', mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Date', 'Acceptance Rate']

    writer = csv.writer(csvfile)
    writer.writerow(fieldnames)

    for date, avg_rate in average_acceptance_by_day.items():
        avg_rate = avg_rate.__trunc__()
        writer.writerow([date, avg_rate])
        print(f"{date}: {avg_rate:.2f}")
