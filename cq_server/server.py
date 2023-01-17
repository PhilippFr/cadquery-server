'''Module server: used to run the Flask web server.'''

import json
from queue import Queue
from typing import Tuple

from flask import Flask, request, render_template, make_response, Response

WATCH_PERIOD = 0.3
SSE_MESSAGE_TEMPLATE = 'event: file_update\ndata: %s\n\n'

app = Flask(__name__, static_url_path='/static')

modules = []


def run(port: int, ui_options: dict) -> None:
    '''Run the Flask web server.'''

    @app.route('/', methods=['GET'])
    def _root() -> str:

        if request.args.get('m'):
            module_data = next(item for item in modules if item["module_name"] == request.args.get('m'))
        elif len(modules) > 0:
            module_data = modules[-1]
        else:
            module_data = {}

        return render_template(
            'viewer.html',
            options=ui_options,
            modules_name=[sub['module_name'] for sub in modules],
            data=module_data or {}
            # data=[ sub['module_name'] for sub in modules ]
        )

    @app.route('/json', methods=['GET'])
    def _json() -> Tuple[str, int]:

        try:
            data = next(item for item in modules if item["module_name"] == request.args.get('m'))
        except StopIteration:
            data = {
                'error': "Module not found"
            }
        return data, (400 if 'error' in data else 200)

    @app.route('/events', methods=['GET'])
    def _events() -> Response:
        def stream():
            while True:
                data = events_queue.get()
                print(f'Sending Server Sent Event: {data[:100]}...')
                yield data

        response = make_response(stream())
        response.mimetype = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-store, must-revalidate'
        response.headers['Expires'] = 0
        return response

    @app.route('/json', methods=['POST'])
    def render_data():
        content_type = request.headers.get('Content-Type')
        if content_type == 'application/json':
            json_model_data = request.json
            print(f'Received render request: {json_model_data}')
            while next((item for item in modules if item["module_name"] == json_model_data["module_name"]), False):
                json_model_data["module_name"] = json_model_data["module_name"] + "-Copy"
            modules.append(json_model_data)
            events_queue.put(SSE_MESSAGE_TEMPLATE % json.dumps(json_model_data))
            return Response(response="Received.", status=200)
        else:
            return 'Content-Type not supported!'

    events_queue = Queue(maxsize=3)

    app.run(host='0.0.0.0', port=port, debug=False)
