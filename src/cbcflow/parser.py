from .core.parser import *

from .core.utils import setup_logger

logger = setup_logger()
logger.info(
    "This message is appearing because you are using deprecated import paths.\n\
            At some point in the future this option will be disabled\n\
            Please use cbcflow.core.parser instead"
)
