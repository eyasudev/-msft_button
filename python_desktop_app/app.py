"""
@
"""

from logging import exception
import ble_app
import team_api_app
import flask_server_app
import logging

from queue import Queue
import threading
import time 


# button mutes and unmute bot itself. 
#This funciton starts call immediately it's called
#and keeps starting call when there is no call presented 

def teams_api_start_call(): 
    team_api_app.init()
    # call_data = team_api_app.make_call()   #captures returned call id 

    #get user and call data, 
    ret_data = team_api_app.init_call_operation()

    if ret_data["ret"] != 0: 
        logging.info("!!!An error occurred while starting application: code{}".format(ret_data["ret"]))
        return

    if ret_data["call_id"] == "" :
        logging.info("!! ---> No call id yet, try making the call again")
        return

    to_mute = False
    prev_to_mute = to_mute

    participant_id = None

    print("[Press the button to mute current call ] ---> MAKE CALL")
    while (True): 
        time.sleep(1)
        # print ("FROM TEAMS API; ble avail: {}, btn: {}".format(ble_app.isBleAlive(), ble_app.button_state))

        if ble_app.isBleAlive():
            to_mute = not ble_app.button_state #pressed is low

        if prev_to_mute != to_mute: 
            prev_to_mute = to_mute

            print("Mute command received, mute? {}".format(to_mute))

            #mute bot
            team_api_app.mute_call(ret_data["call_id"], to_mute)

            #mute the bot caller      
            #first find the participant ID if there is None yet
            if participant_id==None: 
                participant_data = team_api_app.get_call_participants(ret_data["call_id"])
                if (participant_data == None):
                    logging.error("!!!No participation data received")
                    continue

                if "value" not in participant_data:
                    logging.error("!!!Error in participation data ")
                    continue
                
                for participant in participant_data["value"]: 
                    try: 
                        if participant["info"]["identity"]["user"]["id"] == ret_data["user_id"]:
                            print("!!Participant id found")
                            participant_id = participant["info"]["participantId"]
                            break
                    except Exception as e:
                        logging.error(e)
                    
                #if participant_id is still None after getting the data, continue loop 
                if participant_id == None: 
                    logging.error("!!!Participant ID not found")
                    continue
            
            team_api_app.mute_participant(ret_data["call_id"], participant_id, to_mute)






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
# Thread_teams_api = threading.Thread(target=teams_api, args=(msft_graph_que, ))
Thread_teams_api = threading.Thread(target=teams_api_start_call, args=( ))

# Thread_flask_serv = threading.Thread(target=flask_server_app.main, args=())

if __name__ == "__main__": 
    Thread_ble.start()
    Thread_teams_api.start()
    flask_server_app.main(msft_graph_que) #this can't be run on a separate thread, has to run on main thread


