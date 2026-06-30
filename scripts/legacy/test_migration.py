import os
from backend.database import engine, Base
from backend.models import *

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
