import pandas as pd
import numpy as np
import sys
import sqlite3
from custom_process_domain import process_domain_normal

def main(input_db, output, name):
  con = sqlite3.connect(input_db)


  # Get Type of database
  TYPE_IS_SAFARI = "TYPE_IS_SAFARI"
  TYPE_IS_CHROME = "TYPE_IS_CHROME"
  TYPE_OF_DB = {
    "db": TYPE_IS_SAFARI,
    "sqlite": TYPE_IS_CHROME,
    "sqlite3": TYPE_IS_CHROME,
  }

  extension = input_db.split(".")[-1]
  TYPE = TYPE_OF_DB[extension]

  # Load Query
  if TYPE == TYPE_IS_CHROME:
    df = pd.read_sql_query("SELECT * from urls", con)
    
    relevant_fields =       ['visit_count', 'url', 'title', 'domain']
    relevant_fields_alias = ['visit_count', 'sample_url', 'sample_title']
    
  elif TYPE == TYPE_IS_SAFARI:
    df = pd.read_sql_query("SELECT * FROM history_items", con)
    
    relevant_fields =       ['visit_count', 'url', 'domain']
    relevant_fields_alias = ['visit_count', 'sample_url']
  else:
    assert(False and "Extension of database is invalid")
    
  # Extract the domain and combine similar url names
  df['domain'] = df['url'].apply(process_domain_normal)
  
  # Get the number of visit counts per domain
  df_grouped_count = df[relevant_fields].groupby('domain').agg(np.sum)

  # Generate the top 50 (without sample data)
  # top_50 = df_grouped_count.sort_values('visit_count', ascending=False)[0:50]
  # top_50.to_csv(output + f'/top_50_plain_{name}.csv')

  # Generate the top 50 with sample data
  # https://stackoverflow.com/a/65784434
  df_grouped_count__with_first = df[relevant_fields].groupby('domain').agg({k: np.sum if k == 'visit_count' else 'first' for k in relevant_fields})
  top_50__with_first = df_grouped_count__with_first[relevant_fields[0:-1]].sort_values('visit_count', ascending=False)[0:50]

  top_50__with_first.to_csv(output + f'/top_50_{name}.csv', header=relevant_fields_alias)

if __name__=='__main__':
  in_directory = sys.argv[1]
  out_directory = sys.argv[2]
  the_name = 'SOME_NAME'

  if len(sys.argv) >= 3:
    the_name = sys.argv[3]

  main(in_directory, out_directory, the_name)
