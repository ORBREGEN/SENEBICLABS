"""
API v1 router — aggregates all sub-routers.

To add a new feature area:
  1. Create app/api/v1/my_feature.py with its own APIRouter
  2. Import and include it here
"""

from fastapi import APIRouter
from app.api.v1 import system, model, patient, interpret, expert, waitlist, project

api_router = APIRouter()

api_router.include_router(system.router)
api_router.include_router(model.router)
api_router.include_router(interpret.router)
api_router.include_router(patient.router)
api_router.include_router(expert.router)
api_router.include_router(waitlist.router)
api_router.include_router(project.router)
