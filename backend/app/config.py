from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Zarqa al Yamama"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"

    # ============================================================================
    # LLM & AI PROVIDERS
    # ============================================================================
    
    # OpenRouter (Primary LLM Provider)
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # DeepSeek (Secondary LLM Provider)
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    
    # OpenAI (Fallback)
    OPENAI_API_KEY: Optional[str] = None

    # Google Gemini (Reasoning/Search)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_ENABLED: bool = False
    GEMINI_DRY_RUN: bool = False
    
    # LLM Model Configuration
    DEFAULT_LLM_PROVIDER: str = "openrouter"
    DEFAULT_LLM_MODEL: str = "nousresearch/hermes-3-llama-3.1-405b:free"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    REASONING_MODEL: str = "deepseek-reasoner"

    # ============================================================================
    # DATA SOURCE API KEYS
    # ============================================================================
    
    # News & Events Intelligence
    NEWSDATA_API_KEY: Optional[str] = None
    NEWSDATA_BASE_URL: str = "https://newsdata.io/api/1"
    GDELT_API_KEY: Optional[str] = None
    NEWSAPI_KEY: Optional[str] = None
    NEWSAPI_BASE_URL: str = "https://newsapi.org/v2"
    
    GNEWS_API_KEY: Optional[str] = None
    GNEWS_BASE_URL: str = "https://gnews.io/api/v4"

    # Political & Conflict Data
    ACLED_API_KEY: Optional[str] = None
    ACLED_EMAIL: Optional[str] = None
    ACLED_BASE_URL: str = "https://api.acleddata.com/acled/read"

    # Elections Data
    ELECTIONS_API_KEY: Optional[str] = None
    ELECTIONS_BASE_URL: Optional[str] = None

    # Legislative Records
    LEGISLATION_API_KEY: Optional[str] = None
    LEGISLATION_BASE_URL: str = "https://api.congress.gov/v3"
    
    # Financial Market Data
    POLYGON_API_KEY: Optional[str] = None
    POLYGON_BASE_URL: str = "https://api.polygon.io"
    ALPHA_VANTAGE_KEY: Optional[str] = None
    
    # ============================================================================
    # DATABASE CONFIGURATION
    # ============================================================================
    
    # PostgreSQL
    DATABASE_URL: str = "postgresql://zarqa:zarqa_pass@postgres:5432/zarqa_db"
    
    # Qdrant (Vector Database)
    QDRANT_URL: str = "https://a186fa7b-3cf7-4f2d-a72b-d64be9a286de.us-east4-0.gcp.cloud.qdrant.io:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "news_embeddings"
    
    # Neo4j (Knowledge Graph)
    NEO4J_URI: str = "neo4j+s://5c491aab.databases.neo4j.io"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j_pass"
    NEO4J_DATABASE: str = "neo4j"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # ============================================================================
    # AGENT CONFIGURATION
    # ============================================================================
    
    TEMPORAL_ANALYST_ENABLED: bool = True
    CONTEXT_INTERPRETER_ENABLED: bool = True
    QUANTIFIER_ENABLED: bool = True
    CRITIC_ENABLED: bool = True
    GOVERNOR_ENABLED: bool = True
    THINK_TANK_ANALYST_ENABLED: bool = True
    POLITICAL_STUDIES_ANALYST_ENABLED: bool = True
    RISK_SCORER_ENABLED: bool = True
    SCENARIO_MODELER_ENABLED: bool = True
    POLICY_IMPACT_ANALYST_ENABLED: bool = True
    ELECTION_FORECASTER_ENABLED: bool = True
    WALLED_GARDEN_ENABLED: bool = True
    REPORT_WRITER_ENABLED: bool = True
    MARKET_CLASSIFIER_ENABLED: bool = True
    EVIDENCE_ANALYST_ENABLED: bool = True

    # ============================================================================
    # DATA SOURCE TOGGLES
    # ============================================================================

    NEWSDATA_ENABLED: bool = True
    GDELT_ENABLED: bool = True
    ACLED_ENABLED: bool = True
    LEGISLATION_ENABLED: bool = True

    DEFAULT_FORECAST_HORIZON_DAYS: int = 30
    CONFIDENCE_THRESHOLD: float = 0.60
    SENTIMENT_WEIGHT: float = 0.3
    VOLATILITY_FACTOR_BASE: float = 1.0

    # ============================================================================
    # REPORT WRITER
    # ============================================================================

    REPORTS_DIR: str = "reports"
    REPORT_FORMAT: str = "txt"
    REPORT_PDF_ENABLED: bool = False
    REPORT_PDF_FONT_PATH: str = "app/assets/fonts/Amiri-Regular.ttf"
    
    # ============================================================================
    # THINK TANK INTELLIGENCE SOURCES
    # ============================================================================
    
    # EU Council Library
    EU_COUNCIL_LIBRARY_URL: str = "https://www.consilium.europa.eu/en/documents-publications/library/"
    EU_COUNCIL_EUREKA_URL: str = "https://www.consilium.europa.eu/en/documents-publications/library/#eureka"
    EU_COUNCIL_COLLECTIONS_URL: str = "https://www.consilium.europa.eu/en/documents-publications/library/#collections"
    EU_COUNCIL_REFRESH_HOURS: int = 24
    
    # Harvard Kennedy School Think Tank Search
    HARVARD_KSG_BASE_URL: str = "https://guides.library.harvard.edu/hks/think_tank_search"
    HARVARD_KSG_US_URL: str = "https://guides.library.harvard.edu/hks/think_tank_search/US"
    HARVARD_KSG_NON_US_URL: str = "https://guides.library.harvard.edu/hks/think_tank_search/non_US"
    HARVARD_KSG_REFRESH_HOURS: int = 168  # Weekly
    
    # UPenn TTCSP (Think Tanks and Civil Societies Program)
    UPENN_TTCSP_URL: str = "https://guides.library.upenn.edu/c.php?g=1035991&p=7509972"
    UPENN_TTCSP_REFRESH_HOURS: int = 720  # Monthly
    
    # NC State Global Think Tanks Database
    NCSTATE_GLOBAL_URL: str = "https://www.lib.ncsu.edu/databases/global-think-tanks"
    NCSTATE_GLOBAL_REFRESH_HOURS: int = 24
    
    # Traditional Think Tank RSS Sources
    RAND_RSS_URL: str = "https://www.rand.org/news/rss.html"
    CARNEGIE_RSS_URL: str = "https://carnegieendowment.org/rss/rss.xml"
    CHATHAM_HOUSE_RSS_URL: str = "https://www.chathamhouse.org/rss-feeds"
    BROOKINGS_BASE_URL: str = "https://www.brookings.edu"
    
    # Think Tank Scraping Configuration
    THINK_TANK_REQUEST_TIMEOUT: int = 30
    THINK_TANK_MAX_REPORTS_PER_SOURCE: int = 20
    THINK_TANK_MIN_RELEVANCE_SCORE: float = 0.15
    THINK_TANK_MAX_RELEVANT_REPORTS: int = 15
    THINK_TANK_USER_AGENT: str = "Zarqa-al-Yamama/1.0 (Research Bot; +https://zarqa.ai)"
    
    # ============================================================================
    # EMBEDDING CONFIGURATION
    # ============================================================================
    
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # ============================================================================
    # THE LIBRARIAN (RETRIEVAL GOVERNANCE)
    # ============================================================================
    
    LIBRARIAN_ENABLED: bool = True
    LIBRARIAN_STRICT_MODE: bool = True  # If True, blocks all domains not in allowlist
    
    # Rate Limiting
    LIBRARIAN_RATE_LIMIT_PER_MINUTE: int = 30
    LIBRARIAN_RATE_LIMIT_BURST: int = 5
    
    # Caching
    LIBRARIAN_CACHE_TTL_HOURS: int = 24
    
    # Domain Allowlist (can be a comma-separated string)
    SOURCE_ALLOWLIST: str = (
        "rand.org,brookings.edu,carnegieendowment.org,chathamhouse.org,"
        "consilium.europa.eu,harvard.edu,upenn.edu,ncsu.edu,"
        "cfr.org,csis.org,atlanticcouncil.org,wilsoncenter.org,"
        "worldbank.org,imf.org,oecd.org,"
        "reuters.com,bloomberg.com,ft.com,wsj.com,economist.com,"
        "aljazeera.com,aawsat.com,gulfnews.com,arabnews.com,"
        "kuna.net.kw,mof.gov.kw,cbk.gov.kw"  # Kuwait specific
    )

    @model_validator(mode='after')
    def validate_gemini_config(self) -> 'Settings':
        if self.GEMINI_ENABLED and not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_ENABLED is True, but GEMINI_API_KEY is not set.")
        return self

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
