from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./sales.db"
    ecount_company_code: str = ""
    ecount_user_id: str = ""
    ecount_api_cert_key: str = ""
    ecount_zone: str = "IB"
    google_sheets_id: str = "1N87NXPJuRNXyuONZOJyIN5iyMdpgmykx_iTGWAZSgW0"
    google_service_account_json: str = ""  # JSON string of service account credentials
    sync_schedule_hour: int = 6  # sync at 6am daily

    class Config:
        env_file = ".env"

settings = Settings()
