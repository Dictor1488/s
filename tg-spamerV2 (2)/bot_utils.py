import datetime

def add_time_prefix(*args):
  current_time = datetime.datetime.now()
  formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
  message = " ".join(map(str, args))
  return f"[{formatted_time}] {message}"

def print_with_time(*args):
  str_with_time = add_time_prefix(*args)
  print(str_with_time)


def append_to_file(file_path, text):
  with open(file_path, 'a') as file:
    file.write(text + '\n')