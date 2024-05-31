import json
from datetime import datetime, timezone
from wsgiref.simple_server import make_server
import pytz


def get_headers(): 
    return  [('Content-type', 'text/html; charset=utf-8')] 

def get_not_found_response(response):
    headers = get_headers()
    response('404 Not Found', headers)
    return [b'Page Not Found']

def get_bad_request_response(message: str, response): 
  headers = get_headers()
  response ('400 Bad Reqest', headers)
  return [message.encode()]

def get_server_application(request, response):
    path = request.get('PATH_INFO','').LSTRIP('/')
    method = request.get('REQUEST_METHOD')
    match method:
      case 'GET':
        return get_current_time(path, response) # текущее время
      case 'POST':
        if path.endswith('api/v1/convert'):
          return convert_time(request, response) # конвертация времени
        elif path.endswith('api/v1/datediff'):
          return date_difference(request, response) # разница между датами
        else: 
          return get_not_found_response(response) # неправильный запрос
      case _:
        print("Unknown method " + method) # неизвестный метод
        return get_not_found_response(response)
        
#  GET метод - получение текущего времени в запрошенной зоне
def get_current_time(timezone_name, response):
  if timezone_name:
    try:
      tz = pytz.timezone(timezone_name)
      current_time = datetime.now(tz)
    except pytz.UnknownTimeZoneError:
      return get_bad_request_response("Unknown time zone", response)
  else:
    current_time = datetime.now(timezone.utc)

  time_format = '%Y-%m-%d %H:%M:%S %Z' # установка формата времени
  response('200 OK', get_headers())
  return [current_time.strftime(time_format).encode()]
  
# POST метод -  преобразование даты/времени из одного часового пояса в другой
def convert_time(request, response):
  length = int(request.get('CONTENT_LENGTH', 0))
  if length <= 0:
    return get_bad_request_response("Content-Length must be great than zero",response)
  data = json.loads(request['wsgi.input'].read(length)) # запрос в формате JSON
  date_string = data.get('date') # получение даты/времени в строковом формате
  target_tz_name = data.get('target_tz') # целевой часовой пояс
  try:
    source_time = datetime.strptime(date_string, '%m.%d.%Y %H:%M:%S') # преобразование в datetime
    source_tz = pytz.timezone(data.get('tz')) # исходный часовой пояс
    target_tz = pytz.timezone(target_tz_name) # целевой часовой пояс
    conversion = source_tz.localize(source_time).astimezone(target_tz).strftime('%Y-%m-%d %H:%M:%S %Z') # конвертация времени
  except (KeyError, ValueError, pytz.UnknownTimeZoneError):
    return get_bad_request_response("Invalid Request", response)

  response('200 OK', get_headers())
  return [conversion.encode()]
  
# POST метод - отдает число секунд между двумя датами
def date_difference(request, response):
  length = int(request.get('CONTENT_LENGTH', 0))
  if length <= 0:
    return get_bad_request_response("Content-Length must be great than zero",response)
    
  data = json.loads(request['wsgi.input'].read(length))
  first_date_string = data.get('first_date') # получение даты/времени в строковом формате
  first_tz_name = data.get('first_tz') # целевой часовой пояс
  second_date_string = data.get('second_date') # получение даты/времени в строковом формате
  second_tz_name = data.get('second_tz') # целевой часовой пояс
  try:
    first_time = datetime.strptime(first_date_string,'%m.%d.%Y %H:%M:%S') # преобразование в datetime
    first_tz = pytz.timezone(first_tz_name) # часовой пояс первой даты
    first_time = first_tz.localize(first_time) # локализация первой даты
    second_time = datetime.strptime(second_date_string, '%I:%M%p %Y-%m-%d') # преобразование в datetime
    second_tz = pytz.timezone(second_tz_name) # часовой пояс ворой даты
    second_time = second_tz.localize(second_time) # локализация второй даты
    time_diff = abs((second_time - first_time).total_seconds())  # Вычисление разницы
  except (KeyError, ValueError, pytz.UnknownTimeZoneError):
    return get_bad_request_response("Invalid Request", response)

  response('200 OK', get_headers())
  return [str(time_diff).encode()]

# Запуск сервера
if __name__ == '__main__':
  port: int 8080
  httpd = make_server('', port, get_server_application)
  print("Server started on port" + str(port) + "...")
  httpd.serve_forever()