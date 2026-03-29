from pydantic import BaseModel, EmailStr

class Settings(BaseModel):
    tmdb_key: str = ""
    jack_url: str = "http://127.0.0.1:9117"
    jack_key: str = ""
    prowlarr_url: str = ""
    prowlarr_key: str = ""
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    site_url: str = "http://31.57.106.229:8800"

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    approved: bool