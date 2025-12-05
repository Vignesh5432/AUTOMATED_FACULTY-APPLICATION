# allocation/_init_.py
from flask import Blueprint

allocation_bp = Blueprint('allocation', __name__, url_prefix='/allocation')


# import modules so routes are registered
from . import hod_squad_assignment
from . import invigilator_assignment
from . import reallocation_logic