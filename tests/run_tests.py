import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timezone
from app.utils.date_utils import datetime_to_core_data_timestamp, core_data_timestamp_to_datetime
from app.services.fifo_service import FifoService, TaxClassification
from app.services.xirr_service import XirrService, CashFlow
from app.services.fi_service import FiService

from tests.test_fifo import TestFifoService
from tests.test_xirr import TestXirrService
from tests.test_fi import TestFiService

if __name__ == '__main__':
    unittest.main()
