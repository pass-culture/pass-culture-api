from models.mediation import upsert_tuto_mediations
from repository.clean_database import clean_all_database
from sandboxes import scripts

def save_sandbox(name, with_clean=True):
    if with_clean:
        clean_all_database()
    upsert_tuto_mediations()
    script_name = "sandbox_" + name
    sandbox_module = getattr(scripts, script_name)
    sandbox_module.save_sandbox()
