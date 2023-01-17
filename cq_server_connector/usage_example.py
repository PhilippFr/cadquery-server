import cadquery as cq
from cadq_server_module import CADQServerModule

api = CADQServerModule("http://localhost:5000/json")

model = cq.Workplane().box(1, 1, 1)

api.render("test_model", model)