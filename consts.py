import re

RT = 385698
COUNTRY_PATTERN = re.compile(r'^[A-Z]{3}$')
YEAR_PATTERN = re.compile(r'(\d{4})')