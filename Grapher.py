import csv
from datetime import datetime
import matplotlib.pyplot as plt

dates = []
acceptance_rates = []

with open('college_emails.csv', mode='r', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # parse data kai acceptance rate
        date = datetime.strptime(row['Date'], '%Y-%m-%d %H:%M:%S')
        acceptance_rate = float(row['Acceptance Rate'])

        dates.append(date)
        acceptance_rates.append(acceptance_rate)

plt.scatter(dates, acceptance_rates, label="Acceptance Rate", color="green", marker="x", s=30)

plt.xlabel('Date')
plt.ylabel('Acceptance Rate (%)')
plt.title('Acceptance Rate vs. Time')
plt.xticks(rotation=45)
plt.tight_layout()

plt.legend()
plt.show()
