from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = ""
    FMP_API_KEY: str = ""
    JWT_SECRET_KEY: str = ""
    DEBUG: bool = True 
    PROJECT_NAME: str = ""
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://127.0.0.1:3000"
    ]
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    ALPACA_PAPER_TRADING: bool = True
    ENABLE_TRADING_BOT: bool = False
    MAX_TRADE_AMOUNT: float = 1000.0
    
    class Config:
        env_file = ".env" 

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT
    @property
    def allowed_origins(self) -> list:
        return self.ALLOWED_ORIGINS

settings = Settings()


def show_current_settings():
    print("Show current Settings")
    print(f"Data base { settings.DATABASE_URL}")
    print(f"API Key {settings.FMP_API_KEY}")
    print(f"Secret_key {settings.JWT_SECRET_KEY}")
    print(f"Debug {settings.DEBUG}")
    print(f"Project Name {settings.PROJECT_NAME}")
    print(f"Version {settings.VERSION}")

    if not settings.DATABASE_URL:
        print("No database URL found")
    
    if not settings.FMP_API_KEY:
        print("No FMP API key found")
    
    if not settings.JWT_SECRET_KEY:
        print("No JWT secret key found")
    
    return True

def get_database_url():
    return settings.DATABASE_URL

def is_debug_mode():
    return settings.DEBUG

def get_api_key():
    return settings.FMP_API_KEY

def get_settings():
    return settings

if __name__ == "__main__":
    show_current_settings()

