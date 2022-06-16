"""
    python sample.py parameters.json

    Receive events here: https://webhook.site/7de9fc35-0d22-4ed1-9240-5b591054abf7

    cliffolawa id: 935b59a2-ebc4-4939-8abc-a64f2491049d"
    jclif6 id: 1f16b850-2642-4236-a7be-46c783b527f0
    cliffordolaw 16ssq: e452b1cb-4cd1-4558-beca-f7aeb71f434a

    https://321e-102-89-32-89.eu.ngrok.io -> http://localhost:5002  



    NB: the data for user id is in endpoints folder
"""

import sys
import json 
import logging 
import time

import requests
import msal

# Optional logging
# logging.basicConfig(level=logging.DEBUG)

#configuration from file system
config_path = "./jsondata/config_param.json"


config = json.load(open(config_path))
endpoint_create_p2p_call = json.load(open("./jsondata/endpointdata/create_p2p_call.json"))
endpoint_create_grp_call = json.load(open("./jsondata/endpointdata/create_grp_call.json"))
endpoint_mute_p2p_call = json.load(open("./jsondata/endpointdata/mute_p2p_call.json"))
endpoint_mute_grp_call = json.load(open("./jsondata/endpointdata/mute_grp_call.json"))
endpoint_answer_p2p_call = json.load(open("./jsondata/endpointdata/answer_p2p_call.json"))

#replace their callbackuri with that from the config 
endpoint_create_p2p_call["callbackUri"] = config["callbackUri"]
endpoint_create_grp_call["callbackUri"] = config["callbackUri"]
endpoint_answer_p2p_call["callbackUri"] = config["callbackUri"]

app = msal.ConfidentialClientApplication(
    config["client_id"], authority=config["authority"],
    client_credential=config["secret"])

# The pattern to acquire a token looks like this.
result = None

def init(): 
    #1. Look up a token from the cache
    # Since we are looking for token for the current app, NOT for an end user,
    # notice we give account parameter as None.
    global result
    result = app.acquire_token_silent(config["scope"], account=None)

    if not result: 
        logging.info("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_for_client(scopes=config["scope"])

    logging.info("Init complete!!... ###")
    

"""
Post and Get endpoints function
"""
def ep_post_req(endpoint, json_data):
    global result
    if "access_token" in result:
        graph_data_raw = requests.post(
            endpoint,
            json=json_data,
            headers={'Authorization': 'Bearer ' + result['access_token']}, )
        try: 
            graph_data = graph_data_raw.json()
            print("Graph API call result: ")
            print(json.dumps(graph_data, indent=2))
            return graph_data
        except Exception as e :
            print(e, file = sys.stderr) 
            print("Graph result raw: {}".format(graph_data_raw))
            return None
            

    print(result.get("error"))
    print(result.get("error_description"))
    print(result.get("correlation_id"))  # You may need this when reporting a bug

    return None

def ep_get_req(endpoint):
    global result
    if "access_token" in result:
        graph_data = requests.get(
            endpoint,
            headers={'Authorization': 'Bearer ' + result['access_token']}, ).json()

        print("Graph API call result: ")
        print(json.dumps(graph_data, indent=2))
        return graph_data

    print(result.get("error"))
    print(result.get("error_description"))
    print(result.get("correlation_id"))  # You may need this when reporting a bug

    return None


"""
Queries to the microsoft graph api
"""
#send a "create call" request to server 
def make_call(): 
    return ep_post_req(config["ep_create_call"], endpoint_create_p2p_call) 

#send a "create call" request to server while using the group call data 
def make_grp_call(): 
    return ep_post_req(config["ep_create_call"], endpoint_create_grp_call) 

#mute a bot on a peer 2 peer or group call 
def mute_call(call_id, to_mute=True): 
    mute_str = "/mute"
    if not to_mute: 
        mute_str="/unmute"

    ep_str = config["ep_create_call"] + "/" + call_id + mute_str
    print("Muting call with endpoint: {}".format(ep_str))

    #mute and unmute use the same post payload "clientContext"
    return ep_post_req(ep_str, endpoint_mute_p2p_call) 

#get a list of participant objects
def get_call_participants(call_id): 
    ep_str = config["ep_create_call"] + "/" + call_id + "/participants"
    print("Getting call participants with endpoint: {}".format(ep_str))
    return ep_get_req(ep_str) 

#get a list of users on the current tenant 
def get_users(): 
    return ep_get_req(config["ep_get_users"]) 

#mute/unmute a participant 
def mute_participant(call_id, participant_id, to_mute=True): 
    mute_str = "/mute"
    if not to_mute: 
        mute_str = "/unmute"
    
    ep_str = config["ep_create_call"] + "/" + call_id + "/participants/" + participant_id + mute_str 
    print("Muting participant with endpoint: {}".format(ep_str))

    #mute and unmute use the same post payload "clientContext"
    return ep_post_req(ep_str, endpoint_mute_grp_call) 


def answer_call(call_id):
    ep_str = config["ep_create_call"] + "/" + call_id + "/answer"
    return ep_post_req(ep_str, endpoint_answer_p2p_call) 

    

"""
    Process received data or notification 
"""

def process_webhook(data):
    try:
        if len(data["value"]) < 1:
            print("No value array found")
            return {"ret":-1}

        value_0 = data["value"][0] #value at index 0 
        if value_0["@odata.type"] != "#microsoft.graph.commsNotification":
            print("Value data not notification")
            return {"ret":-2}

        resourceData = value_0["resourceData"]
        if resourceData["state"] != "incoming":
            print("Notification not an incoming call")
            return {"ret":-3}

        #GET call id, resourceUrl, and participant id, these are the data needed for putting 
        callId = resourceData["id"]
        resourceUrl = value_0["resourceUrl"]
        participantId = resourceData["source"]["id"]

        return {"ret":0,"callId":callId, "participantId":participantId}#, "resourceUrl":resourceUrl}
        
    except Exception as e: 
        print(e, file = sys.stderr)
        return {"ret":-99}

    


"""
#application functions
"""
def command_prompt(): 
    print("[0] ---> MAKE CALL")
    print("[1] ---> MAKE GROUP CALL")
    print("[2] ---> MUTE CALL")
    print("[3] ---> GET CALL PARTICIPANTS")
    print("[4] ---> GET users")
    print("[5] ---> MUTE/UNMUTE PARTICIPANT")

    return int(input("\n Enter command index: "))

def main():
    init()
    call_data = None    #captures returned call id 
    participant_data = None    #captures returned call id 

    while (True): 
        index = command_prompt()
        if (index == 0):
            call_data = make_call()
        
        elif (index == 1):
            call_data = make_grp_call()

        elif (index == 2): 
            if (call_data == None or call_data["id"] == ""):
                print("!! ---> No call id yet")
                continue

            to_mute = input("\n Do you want to mute? [y: mute/ n: unmute]: ")

            if (to_mute.lower()[0] == 'y'):
                mute_call(call_data["id"])
            else: 
                mute_call(call_data["id"], False)

        elif (index == 3): 
            if (call_data == None or call_data["id"] == ""):
                print("!! ---> No call id yet")
                continue
            participant_data = get_call_participants(call_data["id"])
        elif (index == 4): 
            get_users() 

        #writing neat code 101 
        elif (index == 5): 
            if (call_data == None): 
                print("!! ---> No call id yet")
                continue
            if (participant_data == None): 
                print("!! ---> No participant data/id yet")
                continue

            print("!! Number of participants: {}".format(len(participant_data["value"])))
            
            participant_index = int(input("\n Select participant (index): "))
            to_mute = input("\n Do you want to mute? [y: mute/ n: unmute]: ")

            if (to_mute.lower()[0] == 'y'):
                mute_participant(call_data["id"]
                , participant_data["value"][participant_index]["id"])
            else: 
                mute_participant(call_data["id"]
                , participant_data["value"][participant_index]["id"], to_mute=False)
            


if __name__ == "__main__":
    main()

