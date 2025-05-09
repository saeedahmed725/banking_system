from datetime import datetime

# Test the date formatting
dt = datetime.now()
print(f'Original: {dt}')
print(f'Formatted: {dt.strftime("%b %d, %Y")}')

# Test with string date
str_date = '2025-05-09 11:51:49.589849'
try:
    parsed_dt = datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S.%f')
    print(f'Original string: {str_date}')
    print(f'Parsed and formatted: {parsed_dt.strftime("%b %d, %Y")}')
except Exception as e:
    print(f'Error parsing date: {e}')
