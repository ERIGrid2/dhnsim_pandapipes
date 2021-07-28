import os
import pytest
import logging
from dh_network_simulator.test import test_dir

logger = logging.getLogger()
for handler in logger.handlers:
    logger.removeHandler(handler)
    logger.setLevel(logging.CRITICAL)


def run_tests():
    pytest.main([test_dir, "-xs"])
    print(test_dir)


if __name__ == "__main__":
    run_tests()
