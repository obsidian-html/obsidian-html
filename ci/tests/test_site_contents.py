import requests
from bs4 import BeautifulSoup

# Under construction

def test(results, description, actual_value, defined_value, operator):
    result = {'success': False, 'description': description, 'msg': ''}
    if operator == 'equals':
        if actual_value == defined_value:
            result['success'] = True
        else:
            result['msg'] = f'Value expected: "{defined_value}" does not match actual value: "{actual_value}".'
    else:
        result['msg'] = f'Operator "{operator}" not implemented.'
    
    results.append(result)

def html_get(path):
    response = requests.get(f"http://localhost:8000/{path}")
    return BeautifulSoup(response.text, features="html5lib")

# Tests
# ----------------------------------------------------------------------
results = []

desc = 'Inner HTML of first H1 on the homepage should be "Example Site"'
val = html_get('').body.find('div', attrs={'class':'container'}).find('h1').text
test(results, desc, val, 'Example Site', 'equals' )







print(results)