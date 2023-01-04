import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn
from zoneinfo import ZoneInfo

import re, string
from datetime import datetime
from dateutil.relativedelta import relativedelta
from custom_process_domain import process_domain_normal
import sys
seaborn.set()

################################################
# Constants
################################################
WINDOWS_EPOCH_MICROSECS      = -11644473600000 * 1000
SAFARI_TIME_UPDATE           = 978307200

# User Defined constants re: filtering data from database
MIN_CHROME_VISIT_DURATION = 5
MAX_CHROME_VISIT_DURATION = 2.88e+10 # 8 hours in microseconds

MIN_SAFARI_SCORE = 5

# Database types
TYPE_IS_SAFARI = "TYPE_IS_SAFARI"
TYPE_IS_CHROME = "TYPE_IS_CHROME"
TYPE_OF_DB = {
  "db": TYPE_IS_SAFARI,
  "sqlite": TYPE_IS_CHROME,
  "sqlite3": TYPE_IS_CHROME,
}

# Productivity labels for Rated Outputs
productivity_to_int_map = {
  'Always Distracted' : -2,
  'Mostly Distracted' : -1,
  'Neutrel' : 0,
  'Mostly Intentional' : 1,
  'Always Intentional' : 2,
}

# Regex
pattern = re.compile('[^\w_-]+')

################################################
# Bin a DF column date timestamp into half hours
################################################
NUMBER_OF_INCREMENTS = 24 * 2
DAY_IN_SECONDS = 60 * 60 * 24
ROUND_TO = DAY_IN_SECONDS / NUMBER_OF_INCREMENTS

def get_half_hour(data: pd.Series) -> pd.Series:
  return (data / ROUND_TO).round().astype(np.int32)

def main(input_db, output_dir, rating_file, start_date_str, user_timezone_str):
  con = sqlite3.connect(input_db)
  
  ################################################
  # Deal with Time Data
  ################################################
  USER_TIMEZONE = ZoneInfo(user_timezone_str)
  TIMEZONE_STRING = user_timezone_str

  split_date_str = start_date_str.split('-')
  START_TIME = datetime(
    int(split_date_str[0]),
    int(split_date_str[1]),
    int(split_date_str[2]), 
    tzinfo=USER_TIMEZONE
  )
  END_TIME = START_TIME + relativedelta(months=+1)

  ################################################
  # Deal with different database types
  ################################################

  # Get Type of database
  split_input_db = input_db.split(".")

  db_name_pre = split_input_db[0].split("/")[-1]
  db_name = pattern.sub('', db_name_pre)

  extension = split_input_db[-1]
  DB_TYPE = TYPE_OF_DB[extension]

  if DB_TYPE == TYPE_IS_CHROME:
    query_get_urls_and_times = """
    SELECT v.id, v.visit_time, v.visit_duration, u.url
    FROM 'visits' as v 
    LEFT JOIN urls u ON u.id = v.url
    """

    TIME_CORRECTION_TO_ADD_TO_VISIT_TIME = WINDOWS_EPOCH_MICROSECS
  elif DB_TYPE == TYPE_IS_SAFARI:
    query_get_urls_and_times = """
    SELECT v.id, v.visit_time, v.score, u.url
    FROM 'history_visits' as v 
    LEFT JOIN history_items u ON u.id = v.history_item
    """
    TIME_CORRECTION_TO_ADD_TO_VISIT_TIME = SAFARI_TIME_UPDATE
  else:
    assert(False and "Extension of database is invalid. Must be '.db' or '.sqlite3'")

  ################################################
  # Formatting for Graphs
  ################################################
  start_date_for_graph = START_TIME.strftime('%a, %b %d, %Y')
  end_date_for_graph = END_TIME.strftime('%a, %b %d, %Y')
  time_for_graph = f"{start_date_for_graph} - {end_date_for_graph}"
  CUSTOM_PARAMS_FOR_GRAPH = f"{db_name}: {time_for_graph}"

  start_date_for_file = START_TIME.strftime('%b-%d-%Y')
  end_date_for_file = END_TIME.strftime('%b-%d-%Y')
  time_for_file = "{}--{}".format(start_date_for_file, end_date_for_file)
  CUSTOM_PARAMS_FOR_FILE = f"{db_name}--{time_for_file}"

  accounting_visit_text = "NOT " if DB_TYPE == TYPE_IS_SAFARI else ""
  ################################################
  # Read the Database
  ################################################

  with sqlite3.connect(DB_FILE) as con:
    visits = pd.read_sql_query(query_get_urls_and_times, con)

  ################################################
  # Process the time
  ################################################

  # Visit time in microseconds (s/1,000,000)
  # https://chromium.googlesource.com/chromium/src/+/lkgr/base/time/time.h

  if DB_TYPE == TYPE_IS_CHROME:
    visit_time_in_ns = (visits['visit_time'] + TIME_CORRECTION_TO_ADD_TO_VISIT_TIME) * 1000
    visits['visit_time_epoch'] = pd.to_datetime(visit_time_in_ns, unit='ns', utc=True).map(lambda x: x.tz_convert(TIMEZONE_STRING))
  elif DB_TYPE == TYPE_IS_SAFARI:
    visit_time_in_ns = (visits['visit_time'] + TIME_CORRECTION_TO_ADD_TO_VISIT_TIME)
    visits['visit_time_epoch'] = pd.to_datetime(visit_time_in_ns, unit='s', utc=True).map(lambda x: x.tz_convert(TIMEZONE_STRING))
  else:
    assert(False and "Extension of database is invalid")

  # Extract the domain and combine similar url names
  visits['domain'] = visits['url'].apply(process_domain_normal)
  
  ratings = pd.read_csv(rating_file, index_col='domain')

  ################################################
  # Filter the Data based on Time + Visit Duration/Score
  ################################################

  greaterthanStartTime = visits['visit_time_epoch'] >= START_TIME
  lessThanEndTime = visits['visit_time_epoch'] <= END_TIME
  visits_this_semester = visits[greaterthanStartTime & lessThanEndTime]

  if 'visit_duration' in visits_this_semester.columns:
    min_visit_option = visits_this_semester[visits_this_semester['visit_duration'] >= MIN_CHROME_VISIT_DURATION]
    min_visit_option = min_visit_option[min_visit_option['visit_duration'] < MAX_CHROME_VISIT_DURATION]
  elif 'score' in visits_this_semester.columns:
    min_visit_option = visits_this_semester[visits_this_semester['score'] >= MIN_SAFARI_SCORE]
  else:
    min_visit_option = visits_this_semester

  final_data = min_visit_option.join(ratings[['manual_rating']], on="domain", how='left')
  final_data['productivity_scale'] = final_data['manual_rating'].map(productivity_to_int_map)
  final_data['time_of_day'] = final_data['visit_time_epoch'].dt.hour * 60 * 60 + final_data['visit_time_epoch'].dt.minute * 60 + final_data['visit_time_epoch'].dt.second

  # Remove N/A
  refined_data = final_data.copy()
  refined_data['productivity_scale'] = refined_data['productivity_scale'].fillna(0)

  ################################################
  # Account for Visit Duration (for Chrome only browsers)
  ################################################
  if DB_TYPE == TYPE_IS_CHROME:
    adj_prod_pre = refined_data.copy()

    DAY_IN_SECONDS = 60 * 60 * 24
    ROUND_TO = DAY_IN_SECONDS / NUMBER_OF_INCREMENTS

    # Make a list for each 30 min block then explode them
    adj_prod_pre['adjusted_time'] = adj_prod_pre[['visit_duration', 'visit_time_epoch']].apply(
      lambda x: np.arange(0, x['visit_duration'] // 1e6, ROUND_TO) + x['visit_time_epoch'].value // 1e9, axis=1)
    adj_prod = adj_prod_pre.explode('adjusted_time')

    adj_prod.dropna(subset=['adjusted_time'], inplace=True)

    adj_prod['adjusted_datetime'] = pd.to_datetime(adj_prod['adjusted_time'], unit='s', utc=True).map(lambda x: x.tz_convert(TIMEZONE_STRING))

    adj_prod['time_of_day'] = adj_prod['adjusted_datetime'].dt.hour * 60 * 60 \
      + adj_prod['adjusted_datetime'].dt.minute * 60 \
      + adj_prod['adjusted_datetime'].dt.second
  else:
    adj_prod = refined_data.copy()

  # Split time_of_day into half hours
  adj_prod['half_hour'] = get_half_hour(adj_prod['time_of_day'])

  ################################################
  # Normalize Data
  ################################################
  adj_prod['normalize_prod'] = adj_prod['productivity_scale']
  positive_sum = adj_prod[adj_prod['productivity_scale'] > 0]['productivity_scale'].sum()
  adj_prod.loc[adj_prod['productivity_scale'] > 0, 'normalize_prod'] /= positive_sum

  negative_count = adj_prod[adj_prod['productivity_scale'] < 0]['productivity_scale'].sum()
  adj_prod.loc[adj_prod['productivity_scale'] < 0, 'normalize_prod'] /= -negative_count

  resetted_index = adj_prod.reset_index().drop('index', axis=1)


  ################################################
  # Plot Productive & Distracting Separately
  ################################################
  productive_data_agg = resetted_index[resetted_index['productivity_scale'] >= 0]
  unproductive_data_agg = resetted_index[resetted_index['productivity_scale'] <= 0]

  plt.figure(figsize=(8, 5))
  seaborn.lineplot(
      x='half_hour',
      y='normalize_prod',
      data=productive_data_agg,
      color='green',
      marker='.',
  )
  seaborn.lineplot(
      x='half_hour',
      y='normalize_prod',
      data=unproductive_data_agg,
      color='orange',
      marker='.',
  )
  plt.axhline(y=0, color='b', linestyle='--', alpha=0.5)
  plt.xticks(np.arange(0, NUMBER_OF_INCREMENTS, NUMBER_OF_INCREMENTS/48), np.arange(0, 48, step=1)//2) # Half Hours

  ax = plt.gca()
  for x in ax.xaxis.get_ticklabels()[1::2]:
    x.set_visible(False)

  plt.title(f"Normalized Productivity ({accounting_visit_text}Accounting for Visit Duration): \n ({CUSTOM_PARAMS_FOR_GRAPH})")
  plt.xlabel("Time (Hour)")
  plt.ylabel("Mean + 95 confidence interval of Normalized Productivity")

  plt.savefig(f"{output_dir}/separate--{CUSTOM_PARAMS_FOR_FILE}.png", bbox_inches='tight')

  ################################################
  # Plot Productive & Distracting Together
  ################################################
  plt.figure(figsize=(8, 5))
  seaborn.lineplot(
      x='half_hour',
      y='normalize_prod',
      data=resetted_index,
      color='red',
      marker='.',
  )
  plt.axhline(y=0, color='b', linestyle='--', alpha=0.5)
  plt.xticks(np.arange(0, NUMBER_OF_INCREMENTS, NUMBER_OF_INCREMENTS/48), np.arange(0, 48, step=1)//2) # Half Hours

  ax = plt.gca()
  for x in ax.xaxis.get_ticklabels()[1::2]:
    x.set_visible(False)

  plt.title(f"Normalized Productivity ({accounting_visit_text}Accounting for Visit Duration): \n ({CUSTOM_PARAMS_FOR_GRAPH})")
  plt.xlabel("Time (Hour)")
  plt.ylabel("Mean + 95 confidence interval of Normalized Productivity")
  plt.savefig(f"{output_dir}/together--{CUSTOM_PARAMS_FOR_FILE}.png", bbox_inches='tight')


if __name__=='__main__':

  if len(sys.argv) < 6:
    print(f"Expecting 4-5 arguments: {sys.argv[0]} DB_FILE OUTPUT_DIR RATING_FILE START_DATE USER_TIMEZONE_STRING='US/Pacific'")
    print(f"python {sys.argv[0]} data/Nathan_History.sqlite3 output/graphs rated-output/my_ratings.csv 2022-09-19 US/Pacific")
    print("Note: the rating file is created using `1-get-top-50-websites.py`")
    exit()

  DB_FILE = sys.argv[1]
  OUTPUT_DIR = sys.argv[2]
  RATING_FILE = sys.argv[3]
  START_DATE_STR = sys.argv[4]

  split_date_str = START_DATE_STR.split('-')
  if len(split_date_str) != 3:
    print("Please format your date like: 2022-12-31")
    exit()

  if len(sys.argv) == 5:
    USER_TIMEZONE_STRING='US/Pacific'
  else:
    USER_TIMEZONE_STRING = sys.argv[5]

  main(DB_FILE, OUTPUT_DIR, RATING_FILE, START_DATE_STR, USER_TIMEZONE_STRING)
