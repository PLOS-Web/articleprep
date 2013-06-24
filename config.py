import logging
import os

# log file location (relative path)
LOGGING_BASE_DIR = os.path.abspath('/var/local/scripts/production/articleprep/log')
if not os.path.exists(LOGGING_BASE_DIR):
    os.makedirs(LOGGING_BASE_DIR)

# formatters
verbose_metadatabuilder_formatter = logging.Formatter('%(asctime)-15s %(name)-10s %(levelname)-8s argv:{meta: %(meta)s, before: %(before)s, after: %(after)s} %(funcName)s:%(lineno)s | %(message)s')

# handlers
console_metadatabuilder_debug = logging.StreamHandler()
console_metadatabuilder_debug.setLevel(logging.DEBUG)
console_metadatabuilder_debug.setFormatter(verbose_metadatabuilder_formatter)

console_metadatabuilder_production = logging.StreamHandler()
console_metadatabuilder_production.setLevel(logging.INFO)
console_metadatabuilder_production.setFormatter(verbose_metadatabuilder_formatter)

metadata_file = logging.FileHandler(os.path.join(LOGGING_BASE_DIR,
                                                   'metadata_builder.log'))
metadata_file.setLevel(logging.DEBUG)
metadata_file.setFormatter(verbose_metadatabuilder_formatter)

# loggers
l = logging.getLogger('metadata_builder')
l.setLevel(logging.DEBUG)
l.addHandler(console_metadatabuilder_production)
l.addHandler(metadata_file)

