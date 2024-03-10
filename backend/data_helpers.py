import time
from collections import defaultdict
from bisect import bisect_left

from pymongo import ReturnDocument
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb://mongodb:27017/"
client = MongoClient(uri)

db = client["cluster0"]


def insert_record(key, value):

    url_mapping_collection = db["url_mappings"]
    mapping_record = {"_id": key, "long_url": value, "timestamp": int(time.time())}
    result = url_mapping_collection.insert_one(mapping_record)

    if result.acknowledged:
        return key
    else:
        return None


def get_url_record(short_key):

    url_mapping_collection = db["url_mappings"]
    result = url_mapping_collection.find_one({"_id": short_key})

    if not result:
        return False
    return result["long_url"]


def update_url_access_analytics(short_key):
    analytics_collection = db["analytics"]

    analytics_collection.update_one(
        {"_id": short_key}, {"$push": {"access_times": int(time.time())}}, upsert=True
    )


def get_and_update_counter():

    counter_collection = db["counter"]
    result = counter_collection.find_one_and_update(
        {"name": "unique_counter_name"},
        {"$inc": {"value": 10000}},
        upsert=True,
        return_document=ReturnDocument.BEFORE,
        projection={"_id": 0, "value": 1},
    )

    # Extract the original value
    if result:
        lower_bound = result.get("value", 10000)
    else:
        lower_bound = 10000

    upper_bound = lower_bound + 10000 - 1

    return lower_bound, upper_bound


def pull_url_analytics(short_key):
    analytics_collection = db["analytics"]
    document = analytics_collection.find_one({"_id": short_key}, {"access_times": 1})

    if not document or "access_times" not in document:
        return {"last_24_hours": 0, "last_week": 0, "all_time": 0}

    access_times = document["access_times"]
    current_time = int(time.time())
    one_day_ago = current_time - 24 * 3600
    one_week_ago = current_time - 7 * 24 * 3600

    # Use binary search to find the start index for each range
    index_day = bisect_left(access_times, one_day_ago)
    index_week = bisect_left(access_times, one_week_ago)

    # Count accesses within the time ranges
    counts = {
        "last_24_hours": len(access_times) - index_day,
        "last_week": len(access_times) - index_week,
        "all_time": len(access_times),
    }

    return counts


def check_connection():
    try:
        client.admin.command("ping")
        print("Pinged the Mongo deployment")

    except Exception as e:
        print(e)
