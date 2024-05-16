import datetime

current_time = datetime.datetime.now().time()
start_time = datetime.time(3)
end_time = datetime.time(18)

if start_time <= end_time and start_time <= current_time < end_time:
  print("true")
elif start_time > end_time and (start_time <= current_time or current_time < end_time):
  print("true")
else:
  print("false")