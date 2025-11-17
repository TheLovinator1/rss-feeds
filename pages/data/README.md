# Key Availability Tracking

This directory contains CSV data tracking the availability of game keys for AMD Gaming promotions over time.

## Files

- **`amd_gaming_keys_available.csv`**: Time-series data of key availability for each promotion
  - `timestamp`: ISO 8601 timestamp when the data was recorded
  - `promotion_id`: Unique identifier for the promotion
  - `title`: Promotion title
  - `slug`: URL-friendly promotion identifier
  - `keys_available`: Number of keys available at that timestamp
  - `status`: Promotion status (active, inactive, etc.)

- **`amd_response.json`**: Latest raw API response from AMD Gaming

## Usage

### Automatic Logging

The CSV is automatically updated each time `main.py` runs (typically via GitHub Actions on a schedule):

```bash
uv run python main.py
```

### Manual Logging

To manually append the current key availability to the CSV:

```bash
uv run python amd/csv_logger.py
```

### Backfill Historical Data from Git

If you want to populate the CSV with historical values captured in this repo's git history, run the backfill script:

```bash
uv run python amd/backfill_from_git.py
```

This walks the history of `pages/data/amd_response.json`, extracts `keysAvailable` per promotion at each commit, and appends rows to `amd_gaming_keys_available.csv` using the commit timestamp (UTC).

### View Summary

To see a text summary of the tracked data:

```bash
uv run python amd/visualize_keys.py
```

## Creating Graphs

Install pandas and matplotlib for data visualization:

```bash
uv add pandas matplotlib
```

Example script to create a line chart:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('pages/data/amd_gaming_keys_available.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Plot for each promotion
for promo_id in df['promotion_id'].unique():
    promo_data = df[df['promotion_id'] == promo_id]
    plt.plot(
        promo_data['timestamp'],
        promo_data['keys_available'],
        marker='o',
        label=promo_data['title'].iloc[0]
    )

plt.xlabel('Date')
plt.ylabel('Keys Available')
plt.title('AMD Gaming Promotions - Key Availability Over Time')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('keys_availability.png')
plt.show()
```

## Data Analysis Ideas

- **Depletion Rate**: Track how quickly keys are claimed over time
- **Promotion Patterns**: Identify which types of promotions get more claims
- **Peak Times**: Determine when users are most active in claiming keys
- **Availability Trends**: Monitor if AMD is increasing/decreasing key allocations

## GitHub Pages

This CSV file is published alongside the RSS feed at:
<https://thelovinator1.github.io/rss-feeds/data/amd_gaming_keys_available.csv>

You can access it programmatically for external analysis or dashboards.
