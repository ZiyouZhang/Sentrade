#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Yiwen Sun"
__status__ = "Production"

import pytest
import datetime
from pymongo import MongoClient

def most_recent_business_day():
    """
    This is the function to find the most recent business day before the current day.
    """
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    current_day = datetime.datetime.now().day
    today = datetime.datetime(current_year, current_month, current_day)

    offset = max(1, (today.weekday() + 6) % 7 - 3)
    timedelta = datetime.timedelta(offset)
    most_recent = str(today - timedelta)[:10]

    return most_recent

def test_date_existence():
    with MongoClient(os.environ["CLIENT_ADDR"]) as client:
        test_business_day = most_recent_business_day()
        db = client.sentrade_db
        stock_db = db.stock_price
        date_exists = stock_db.find_one({"date": test_business_day}) != None
        assert date_exists


if __name__ == "__main__":
    pass