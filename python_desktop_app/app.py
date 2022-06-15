import ble_app
import threading
import time 

def teams_api(): 
    while True:
        time.sleep(2)
        print ("FROM API; ble avail: {}, btn: {}".format(ble_app.isBleAlive(), ble_app.button_state))

#for multi threading 
thrd_lock = threading.Lock()
Thread_ble = threading.Thread(target=ble_app.main, args=())
Thread_teams_api = threading.Thread(target=teams_api, args=())

if __name__ == "__main__": 
    # ble_app.main()
    Thread_ble.start()
    Thread_teams_api.start()

