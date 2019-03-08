# request library
import requests
from tornado import httpclient, ioloop
from colorama import init,Fore, Style
import time
import datetime
import schedule
init()

i = 0

#Def for a request, stops when the looper is 0
def handle_request(Req):
    #Failed requests for testing
    if (Req.code == 599):
        print('\n',Fore.RED + 'Request Code, FAIL = ' ,Req.code, '\n')
        print(Style.RESET_ALL)
    else:
    #Successful requests for testing
        if (Req.code == 200):
             print('\n',Fore.GREEN + 'Request Code, SUCCESS = ' ,Req.code, '\n')
             print(Style.RESET_ALL)

    print(type(Req), '\n')
    # If you want to print headers, uncomment this
    #print('Request Headers = ',Req.headers)
    global i
    i -= 1
    if i == 0:
        ioloop.IOLoop.instance().stop()

#Requests Looper, you can change the IP of the server down below
def Random_Requester(Number_Of_Requests):
    http_client = httpclient.AsyncHTTPClient()
    global i
    for x in range(Number_Of_Requests):
        i += 1
    #Send data to this IP
        http_client.fetch("http://54.147.181.67", handle_request, method='HEAD')
    ioloop.IOLoop.instance().start()

#Printings
def print_running():
    Date = datetime.datetime.now()
    print(Fore.CYAN + "Schedular is currently running 500 Requests")
    print(Date.strftime("%Y-%m-%d %H:%M"))
    print(Style.RESET_ALL)

#########

#Schedual jobs, you can edit them as you like. Read the docs for better understanding of the library and regex
#Change the numbers at the end to whatever you want as the number of requests
schedule.every(1).minutes.do(print_running)
schedule.every(1).to(7).days.do(Random_Requester, 1)
schedule.every(1).to(7).days.do(Random_Requester, 3000)
 
#Infinite while that runs the schedualer
while True:
    schedule.run_pending() 
    time.sleep(1)
