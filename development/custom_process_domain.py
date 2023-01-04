"""
A more complicated regex to extract domain + first subdirectory
"""
import re

# Match https://*/
regex_extract_domain = re.compile('^[^/]+://([^/]+/?[^/\?]*)')

# Match file:///* and data:image/*
regex_extract_domain_temp = re.compile('^([^/]+:/+[^/]+/?[^/\?]*|data:[^/]+)')
def extract_domain_with_regex(url: str):
  m = regex_extract_domain.match(url)
  try:
    domain = m.group(1)
  except AttributeError:
    m2 = regex_extract_domain_temp.match(url)

    try:
      domain = m2.group(1)
    except AttributeError:
      domain = "ERROR"

  return domain

"""
A simple function to extract the domain
"""
def extract_domain_with_string_funcs(url:str):
  start = url.find('//') + 2
  end = url.find('/', start)
  return url[start:end]


"""
Process the domain
"""
map_domains = {
  'google.ca/maps': 'google.com/maps',
  'google.ca': 'google.com',
}

def process_domain_normal(url:str):
  domain : str = extract_domain_with_string_funcs(url)
  domain = domain.strip('/')
  domain = domain.removeprefix('www.').removeprefix('www2.')

  if (domain in map_domains):
    return map_domains[domain]
  else:
    return domain
  