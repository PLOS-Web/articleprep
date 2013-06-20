import logging.config
import os

# log file location (relative path)
LOGGING_BASE_DIR = os.path.abspath('logs')
if not os.path.exists(LOGGING_BASE_DIR):
    os.makedirs(LOGGING_BASE_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose-metadatabuilder': {
            'format': '%(asctime)-15s %(name)-10s %(levelname)-8s argv:{meta: %(meta)s, before: %(before)s, after: %(after)s} %(funcName)s:%(lineno)s | %(message)s'
        },
    },
    'handlers': {
        'console-metadatabuilder-debug':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose-metadatabuilder'
        },
        'console-metadatabuilder-production':{
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter': 'verbose-metadatabuilder'
        },
        'metadata-file':{
            'level': 'DEBUG',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'filename': os.path.join(LOGGING_BASE_DIR, 'metadata_builder.log'), #log filename
            'backupCount': '10',
            'formatter': 'verbose-metadatabuilder',
            },
    },
    'loggers': {
        'metadata_builder': {
            'handlers':['console-metadatabuilder-production', 'metadata-file'],
            'propagate': True,
            'level':'DEBUG',
        },
    }
}

logging.config.dictConfig(LOGGING)
