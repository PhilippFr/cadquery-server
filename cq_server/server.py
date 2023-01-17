'''Module server: used to run the Flask web server.'''

import json
from threading import Thread
from queue import Queue
from time import sleep
from typing import Tuple

from flask import Flask, request, render_template, make_response, Response

WATCH_PERIOD = 0.3
SSE_MESSAGE_TEMPLATE = 'event: file_update\ndata: %s\n\n'

app = Flask(__name__, static_url_path='/static')

modules = [{'module_name': 'test_model_default', 'model': [{'parts': [{'id': '/Group/Part_0', 'type': 'shapes', 'name': 'Part_0', 'shape': {'vertices': [-0.5, -0.5, -0.5, -0.5, -0.5, 0.5, -0.5, 0.5, -0.5, -0.5, 0.5, 0.5, 0.5, -0.5, -0.5, 0.5, -0.5, 0.5, 0.5, 0.5, -0.5, 0.5, 0.5, 0.5, -0.5, -0.5, -0.5, 0.5, -0.5, -0.5, -0.5, -0.5, 0.5, 0.5, -0.5, 0.5, -0.5, 0.5, -0.5, 0.5, 0.5, -0.5, -0.5, 0.5, 0.5, 0.5, 0.5, 0.5, -0.5, -0.5, -0.5, -0.5, 0.5, -0.5, 0.5, -0.5, -0.5, 0.5, 0.5, -0.5, -0.5, -0.5, 0.5, -0.5, 0.5, 0.5, 0.5, -0.5, 0.5, 0.5, 0.5, 0.5], 'triangles': [1, 2, 0, 1, 3, 2, 5, 4, 6, 5, 6, 7, 11, 8, 9, 11, 10, 8, 15, 13, 12, 15, 12, 14, 19, 16, 17, 19, 18, 16, 23, 21, 20, 23, 20, 22], 'normals': [-1.0, -0.0, 0.0, -1.0, -0.0, 0.0, -1.0, -0.0, 0.0, -1.0, -0.0, 0.0, 1.0, 0.0, -0.0, 1.0, 0.0, -0.0, 1.0, 0.0, -0.0, 1.0, 0.0, -0.0, -0.0, -1.0, -0.0, -0.0, -1.0, -0.0, -0.0, -1.0, -0.0, -0.0, -1.0, -0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, -0.0, -0.0, -1.0, -0.0, -0.0, -1.0, -0.0, -0.0, -1.0, -0.0, -0.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0], 'edges': [[[-0.5, -0.5, -0.5], [-0.5, -0.5, 0.5]], [[-0.5, -0.5, 0.5], [-0.5, 0.5, 0.5]], [[-0.5, 0.5, -0.5], [-0.5, 0.5, 0.5]], [[-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5]], [[0.5, -0.5, -0.5], [0.5, -0.5, 0.5]], [[0.5, -0.5, 0.5], [0.5, 0.5, 0.5]], [[0.5, 0.5, -0.5], [0.5, 0.5, 0.5]], [[0.5, -0.5, -0.5], [0.5, 0.5, -0.5]], [[-0.5, -0.5, -0.5], [0.5, -0.5, -0.5]], [[-0.5, -0.5, 0.5], [0.5, -0.5, 0.5]], [[-0.5, 0.5, -0.5], [0.5, 0.5, -0.5]], [[-0.5, 0.5, 0.5], [0.5, 0.5, 0.5]]]}, 'color': '#e8b024', 'alpha': 1.0, 'renderback': False, 'accuracy': 0.001, 'bb': {'xmin': -0.5, 'xmax': 0.5, 'ymin': -0.5, 'ymax': 0.5, 'zmin': -0.5, 'zmax': 0.5}}], 'loc': None, 'name': 'Group'}, {'/Group/Part_0': [1, 1]}], 'source': ''}]

newModel = False

def run(port: int, ui_options: dict, is_dead: bool=False) -> None:
    '''Run the Flask web server.'''

    @app.route('/', methods = [ 'GET' ])
    def _root() -> str:

        return render_template(
            'viewer.html',
            options=ui_options,
            modules_name=list(),
            data=modules[-1]
            #data=[ sub['module_name'] for sub in modules ]
        )

    @app.route('/json', methods = [ 'GET' ])
    def _json() -> Tuple[str, int]:

        data = next(item for item in modules if item["name"] == request.args.get('m'))
        return data, (400 if 'error' in data else 200)

    @app.route('/events', methods = [ 'GET' ])
    def _events() -> Response:
        def stream():
            while True:
                data = events_queue.get()
                print(f'Sending Server Sent Event: { data[:100] }...')
                yield data

        response = make_response(stream())
        response.mimetype = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-store, must-revalidate'
        response.headers['Expires'] = 0
        return response

    @app.route('/json', methods=['POST'])
    def render_data():
        global newModel
        content_type = request.headers.get('Content-Type')
        if content_type == 'application/json':
            json_model_data = request.json
            # TODO
            print(f'Received render request: { json_model_data }')
            modules.append(json_model_data)
            events_queue.put(SSE_MESSAGE_TEMPLATE % json.dumps(json_model_data))
            newModel = True
            #events_queue.put(SSE_MESSAGE_TEMPLATE % json.dumps(json_model_data))
            return Response(response="Received.", status=200)
        else:
            return 'Content-Type not supported!'

    def watchdog() -> None:
        global newModel
        while True:

            if newModel and False:
                data = modules
                print("Watchdog: ")
                print(json.dumps(data))
                events_queue.put(SSE_MESSAGE_TEMPLATE % json.dumps(data))
                newModel = False
            sleep(WATCH_PERIOD)

    events_queue = Queue(maxsize = 3)

    if not is_dead:
        watchdog_thread = Thread(target=watchdog, daemon=True)
        watchdog_thread.start()

    app.run(host='0.0.0.0', port=port, debug=False)
