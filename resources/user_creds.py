import os
from dotenv import load_dotenv

load_dotenv()


class SuperAdminCreds:
    USERNAME = os.getenv("SUPER_ADMIN_USERNAME", "api1@gmail.com")
    PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "asdqwe123Q")