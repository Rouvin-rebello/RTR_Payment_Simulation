import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Load data
df = pd.read_csv("output/transaction data.csv", parse_dates=["timestamp"])

# Extract date and hour
df['date'] = df['timestamp'].dt.date
df['hour'] = df['timestamp'].dt.hour

# 1. Volume & Trend Analysis
# --------------------------

# Daily transaction volume
daily_volume = df.groupby('date').size()
print("\nDaily Transaction Volume:\n", daily_volume)

# Total and average amount per day
daily_amount = df.groupby('date')['amount'].agg(['sum', 'mean'])
print("\nTotal and Average Amount Per Day:\n", daily_amount)

# Hourly trends
hourly_trend = df.groupby('hour').size()
print("\n⏱Hourly Transaction Trends:\n", hourly_trend)

# 2. Status-Based Analysis
# ------------------------

# Success vs Failure count and ratio
status_counts = df['status_clean'].value_counts()
print("\nStatus Count:\n", status_counts)

status_ratio = status_counts / status_counts.sum()
print("\nStatus Ratio:\n", status_ratio)

# Failure rate over time
failure_rate = df.groupby('date')['status_clean'].apply(
    lambda x: (x == 'Failure').sum() / len(x))
print("\nFailure Rate by Day:\n", failure_rate)

# Frequent failure messages
failure_messages = df[df['status_clean'] == 'Failure']['status'].value_counts()
print("\nFrequent Failure Messages:\n", failure_messages)

# 3. Top Participants
# -------------------

# Top senders
top_senders = df.groupby('sender')['amount'].sum().sort_values(ascending=False)
print("\nTop Senders by Amount:\n", top_senders)

# Top receivers
top_receivers = df.groupby('receiver')['amount'].sum().sort_values(ascending=False)
print("\nTop Receivers by Amount:\n", top_receivers)

# FI performance (sender BIC)
fi_performance = df.groupby('sender_bic')['amount'].sum().sort_values(ascending=False)
print("\nFI Performance (Sender BIC):\n", fi_performance)

# 4. Net Flow Analysis
# ---------------------

sent = df.groupby('sender')['amount'].sum()
received = df.groupby('receiver')['amount'].sum()
net_flow = (received - sent).fillna(0).sort_values()
print("\nNet Flow Per Entity:\n", net_flow)

# Balance trend per day
sent_daily = df.groupby(['date', 'sender'])['amount'].sum().unstack().fillna(0)
received_daily = df.groupby(['date', 'receiver'])['amount'].sum().unstack().fillna(0)
net_balance_daily = received_daily - sent_daily
print("\nDaily Net Balance (Partial):\n", net_balance_daily.head())

# 5. Correlation & Patterns
# --------------------------

# Avg amount by status
avg_by_status = df.groupby('status_clean')['amount'].mean()
print("\nAvg Amount by Status:\n", avg_by_status)

# Avg amount by sender
avg_by_sender = df.groupby('sender')['amount'].mean()
print("\nAvg Amount by Sender:\n", avg_by_sender)

# Time between transactions
df_sorted = df.sort_values('timestamp')
df_sorted['time_diff'] = df_sorted['timestamp'].diff().dt.total_seconds()
print("\nTime Between Transactions (seconds):\n", df_sorted[['timestamp', 'time_diff']].head())

# Recurring pairs
pair_counts = df.groupby(['sender', 'receiver']).size().sort_values(ascending=False)
print("\nRecurring Sender/Receiver Pairs:\n", pair_counts.head())

# 6. Anomaly Detection (Simple)
# -----------------------------

# Very large or small transactions
threshold_high = df['amount'].quantile(0.95)
threshold_low = df['amount'].quantile(0.05)
anomalies = df[(df['amount'] > threshold_high) | (df['amount'] < threshold_low)]
print("\nLarge/Small Transaction Anomalies:\n", anomalies[['timestamp', 'sender', 'receiver', 'amount']])

# Unusual hours
odd_hours = df[(df['hour'] < 6) | (df['hour'] > 22)]
print("\nTransactions at Odd Hours:\n", odd_hours[['timestamp', 'sender', 'receiver', 'amount']])

# Sudden spike in failure rate
failure_spike = failure_rate[failure_rate > 0.3]
print("\nDays with High Failure Rate:\n", failure_spike)

# Questions
# -------------------

# Which FI sends the most?
most_sent_fi = df.groupby('sender_bic')['amount'].sum().idxmax()
print(f"\nFI sending most money: {most_sent_fi}")

# Average transaction size by sender
avg_size_sender = df.groupby('sender')['amount'].mean().sort_values(ascending=False)
print("\nAvg Transaction Size by Sender:\n", avg_size_sender)

# Day with most transactions
busiest_day = daily_volume.idxmax()
print(f"\nBusiest Transaction Day: {busiest_day}")

# Failed transactions
failed_txns = df[df['status_clean'] == 'Failure'][['timestamp', 'transaction_id', 'status']]
print("\nFailed Transactions:\n", failed_txns)


sns.countplot(data=df, x='hour')
plt.title("Hourly Transaction Volume")
plt.show()

daily_volume.plot(kind='bar', title="Transactions Per Day")
plt.show()
