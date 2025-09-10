from fastapi import FastAPI

from ai_cv_parsing.routes import cvs


app = FastAPI()
app.include_router(cvs.router)