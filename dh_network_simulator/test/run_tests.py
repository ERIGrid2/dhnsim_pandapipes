import os
import pytest
import logging

logger = logging.getLogger()
for handler in logger.handlers:
    logger.removeHandler(handler)
    logger.setLevel(logging.CRITICAL)

def _get_test_dir(pp_module=None):
    # helper function to get the test dir and check if it exists
    test_dir = test_path
    if pp_module is not None and isinstance(pp_module, str):
        test_dir = os.path.join(test_dir, pp_module)
    if not os.path.isdir(test_dir):
        raise ValueError("test_dir {} is not a dir".format(test_dir))
    return test_dir


def run_tests():
    test_dir = _get_test_dir()
    pytest.main([test_dir, "-xs"])


if __name__ == "__main__":
    run_tests()
