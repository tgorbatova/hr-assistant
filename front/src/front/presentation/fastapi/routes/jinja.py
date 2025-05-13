from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown import markdown
from starlette.templating import Jinja2Templates

from front.main.config import settings

env = Environment(
    autoescape=select_autoescape(["html", "xml"]), loader=FileSystemLoader(settings.APP.TEMPLATES_DIRECTORY)
)


env.filters["markdown"] = markdown
env.globals["ssl"] = settings.APP.CLIENT_SECURE_REQUESTS
templates = Jinja2Templates(env=env)
