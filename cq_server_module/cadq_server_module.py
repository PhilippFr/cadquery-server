import json
import sys

import requests
from cadquery import Assembly, Color
from cadquery.cqgi import CQModel
from jupyter_cadquery.base import _tessellate_group
from jupyter_cadquery.cad_objects import to_assembly
from jupyter_cadquery.utils import numpy_to_json


def get_json_model(assembly_children) -> list:
    """Return the tesselated model of the assembly,
    as a dictionnary usable by three-cad-viewer."""

    try:
        jcq_assembly = to_assembly(assembly_children)
        assembly_tesselated = _tessellate_group(jcq_assembly)
        assembly_json = numpy_to_json(assembly_tesselated)
    except Exception as error:
        raise CADQServerModuleError('An error occured when tesselating the assembly.') from error

    return json.loads(assembly_json)


def get_result(cq_model: CQModel):
    """Return a CQ assembly object composed of all models passed
    to show_object and debug functions in the CadQuery script."""

    result = cq_model.build()

    if not result.success:
        raise CADQServerModuleError('Error in model', result.exception)

    return result


def get_assembly(build_result):
    MODEL_COLOR_DEFAULT = Color(0.9, 0.7, 0.1)
    MODEL_COLOR_DEBUG = Color(1, 0, 0, 0.2)

    assembly = Assembly()

    for counter, result in enumerate(build_result.results):
        rgb = result.options.get('color', None)
        alpha = result.options.get('alpha', None)
        name = result.options.get('name', None)

        color = rgb if isinstance(rgb, Color) \
            else Color(rgb) if isinstance(rgb, str) \
            else Color(*rgb) if isinstance(rgb, tuple) \
            else MODEL_COLOR_DEFAULT

        if alpha:
            color = Color(color.toTuple()[:3] + [alpha])

        try:
            assembly.add(result.shape, color=color, name=name)
        except ValueError:
            assembly.add(result.shape, color=color, name=f'{name}_{counter}')

    for result in build_result.debugObjects:
        assembly.add(result.shape, color=MODEL_COLOR_DEBUG)

    if not assembly.children:
        raise ValueError('nothing to show')

    return assembly


def get_data(module_name, json_model) -> dict:
    """Return the data to send to the client, that includes the tesselated model."""

    data = {}

    try:
        data = {
            'module_name': module_name,
            'model': json_model,
            'source': ''
        }
    except CADQServerModuleError as error:
        raise (error)

    return data


class CADQServerModule:

    def __init__(self, url):
        self.url = url

    def render(self, name, cq_model):
        result = get_result(cq_model)
        assembly = get_assembly(result)
        json_model = get_json_model(*assembly.children)
        json_data = get_data(name, json_model)
        self.post_data(json_data)

    def post_data(self, data):
        # sending post request and saving response as response object
        r = requests.post(url=self.url, data=data, timeout=20)

        # extracting response text 
        resp = r.text
        print(f"Render Response:{resp}")
        return r


class CADQServerModuleError(Exception):
    """Error class used to define ModuleManager errors."""

    def __init__(self, message: str, stacktrace: str = ''):
        self.message = message
        self.stacktrace = stacktrace

        print('Module manager error: ' + message, file=sys.stderr)
        if stacktrace:
            print(stacktrace, file=sys.stderr)

        super().__init__(self.message)
