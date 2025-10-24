import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'devkey'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    
    # Data file paths
    DATA_KIXIE = os.environ.get('DATA_KIXIE', './data/kixie_call_history.csv')
    DATA_TELESIGN_WITH = os.environ.get('DATA_TELESIGN_WITH', './data/telesign_with_live.csv')
    DATA_TELESIGN_WITHOUT = os.environ.get('DATA_TELESIGN_WITHOUT', './data/telesign_without_live.csv')
    DATA_POWERLIST = os.environ.get('DATA_POWERLIST', './data/powerlist_contacts.csv')
    
    # Configuration parameters
    DEFAULT_DIAL_AT_A_TIME = int(os.environ.get('DEFAULT_DIAL_AT_A_TIME', 4))
    DEFAULT_MAX_ATTEMPTS = int(os.environ.get('DEFAULT_MAX_ATTEMPTS', 10))
    DEFAULT_ATTEMPTS_PER_DAY = int(os.environ.get('DEFAULT_ATTEMPTS_PER_DAY', 2))
    COOLDOWN_DAYS = int(os.environ.get('COOLDOWN_DAYS', 14))
    PILOT_LIST_NAME = os.environ.get('PILOT_LIST_NAME', 'NAICS')
    TARGET_CONNECT_UPLIFT_PCT = int(os.environ.get('TARGET_CONNECT_UPLIFT_PCT', 30))
    SUCCESS_CRITERIA_CONNECT_UPLIFT_PCT = int(os.environ.get('SUCCESS_CRITERIA_CONNECT_UPLIFT_PCT', 25))
    SUCCESS_CRITERIA_VOICEMAIL_UPLIFT_PCT = int(os.environ.get('SUCCESS_CRITERIA_VOICEMAIL_UPLIFT_PCT', 15))
    TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Manila')
    
    # Connect dispositions (configurable set)
    CONNECT_DISPOSITIONS = {'Connected', 'Left voicemail'}

