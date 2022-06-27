from flask import Flask, jsonify, json, render_template, url_for, request, redirect, make_response
import os
from queue import Queue

msft_graph_que = None

"""
Flask server for receiving call webhook
"""
app = Flask(__name__)

#send data to queue 
def handle_msft_graph_webhook(data): 
    global msft_graph_que
    if msft_graph_que == None: 
        return
    msft_graph_que.put(data)
    

@app.route('/', methods=['GET','POST'])
def index(): 
    data = request.get_json()
    # print("Got Request: {} \n\nData: {}".format(request, data))
    handle_msft_graph_webhook(data)
    return jsonify({'msg':'test'})

def main(que = None):
    global msft_graph_que
    msft_graph_que = que

    port = int(os.environ.get('PORT',5002))
    # http://localhost:5002/
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)
    # use_reloader=False -> ensures that the script ins't ran twice


if __name__ == "__main__":
    main()


