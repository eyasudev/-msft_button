"""
@
"""

import ble_app
import team_api_app
import flask_server_app

from queue import Queue
import threading
import time 


# button mutes and unmute bot itself. 
#This funciton starts call immediately it's called
#and keeps starting call when there is no call presented 
def teams_api_start_call(): 
    team_api_app.init()
    # call_data = team_api_app.make_call()   #captures returned call id 

    call_data = team_api_app.make_grp_call()   #captures returned call id 

    to_mute = False
    prev_to_mute = to_mute
    

    print("[Press the button to mute current call ] ---> MAKE CALL")
    while (True): 
        time.sleep(1)
        print ("FROM TEAMS API; ble avail: {}, btn: {}".format(ble_app.isBleAlive(), ble_app.button_state))

        if ble_app.isBleAlive():
            to_mute = not ble_app.button_state #pressed is low
    
        if (call_data == None or call_data["id"] == ""):
            print("!! ---> No call id yet")
            call_data = team_api_app.make_call()   #captures returned call id 
            continue

        if prev_to_mute != to_mute: 
            print("Mute command received, mute? {}".format(to_mute))
            team_api_app.mute_call(call_data["id"], to_mute)

        prev_to_mute = to_mute

# button mutes and unmute bot itself. 
#This function waits for incoming call and join
#Then uses the esp32 btn to mute and unmute itself 
def teams_api(que): 
    team_api_app.init()

    # call_data = None 
    notification_data = {"ret":-98}

    to_mute = False
    prev_to_mute = to_mute

    print("[Press the button to mute current call ] ---> MAKE CALL")
    while (True): 
        time.sleep(1)
        # print ("FROM API; ble avail: {}, btn: {}".format(ble_app.isBleAlive(), ble_app.button_state))

        if not que.empty(): 
            data = que.get();
            print("\n\nQueue is not empty data: {}".format(data))
            
            #process data team_api_app
            ret_pro = team_api_app.process_webhook(data)
            print("\n\nProcessed data: {}".format(ret_pro))

            if ret_pro["ret"] == 0: #good incoming call message
                notification_data = ret_pro
                team_api_app.answer_call(ret_pro["callId"])
                # {'ret': 0, 'callId': '661f6100-5680-43a0-9e92-60c21c76608f','participantId': '4b2535c8-f091-4ffb-82fd-66e724d93d2a', 'resourceUrl': '/communications/calls/661f6100-5680-43a0-9e92-60c21c76608f'}

        if ble_app.isBleAlive():
            to_mute = not ble_app.button_state #pressed is low
    
        #SEND mute command 
        if prev_to_mute != to_mute: 
            print("Mute command received, mute? {}".format(to_mute))
            if notification_data["ret"] == 0: 
                print("Call id present.. muting / unmuting")
                #mute bot
                team_api_app.mute_call(notification_data["callId"], to_mute)

                #mute the bot caller
                team_api_app.mute_participant(notification_data["callId"]
                , notification_data["participantId"], to_mute)

            else: 
                print("No call id present ")

            

        prev_to_mute = to_mute

# Create the shared queue and launch threads
msft_graph_que = Queue()

#for multi threading 
thrd_lock = threading.Lock()
Thread_ble = threading.Thread(target=ble_app.main, args=( ))
Thread_teams_api = threading.Thread(target=teams_api, args=(msft_graph_que, ))
# Thread_flask_serv = threading.Thread(target=flask_server_app.main, args=())

if __name__ == "__main__": 
    Thread_ble.start()
    Thread_teams_api.start()
    flask_server_app.main(msft_graph_que)


