#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import string
import tweepy as tw
import pandas as pd
import json
import re
import emoji
import time
import sys
from datetime import datetime
from textblob import TextBlob
from pathlib import Path
from pymongo import MongoClient

__author__ = "Ziyou Zhang, Fenming Liu"
__status__ = "Development"

month_map = {"Jan": "01", 
             "Feb": "02",
             "Mar": "03",
             "Apr": "04",
             "May": "05",
             "Jun": "06",
             "Jul": "07",
             "Aug": "08",
             "Sep": "09",
             "Oct": "10",
             "Nov": "11",
             "Dec": "12"
            }

def parse_twitter_date(date):
    """
    Change the format of the twitter date string.

    :param date: the original date string. e.g. "Fri Jan 03 16:34:09 +0000 2020"
    
    :return: reformated string. e.g. 2020-01-03
    """
    new_date = ""
    
    year = date[-4:]
    month = date[4:7]
    day = date[8:10]
    month = month_map[month]

    new_date = year + "-" + month + "-" + day
    return new_date

def process_original_tweet(text):
    """
    Process the original text.

    :param text: original tweet text.
    :return: the processed tweet text.
    """

    text = re.sub(pattern=re.compile(r'RT @(.*?):(\s)'), repl='', string=text)
    text = re.sub(pattern=re.compile(r'http\S+'), repl='', string=text)
    text = re.sub(pattern=emoji.get_emoji_regexp(), repl='', string=text)
    text = "".join([i if i.isalnum() or i in string.whitespace else '' for i in text])
    text = text.lower()

    return text

def scrap_tweets_today(company_name):
    consumer_key = "o62Qbz4RQcWoSlZwYAf8rk6Br"
    consumer_secret = "rIA9adduzHxl6lude0lCNYoyNy00trNTsGmrlHNR1M5anasaeB"
    access_token = "1079882101191778305-UxW9ONHBCHTsHYlfBcWBqsNVmJ7a70"
    access_token_secret = "0TSs4ls9OYedbFBNhGr72vXgWPkWoFJxDd8Fwj8TpT9jD"

    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tw.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    search = company_name + " -filter:retweets"
    date_since = datetime.today().strftime('%Y-%m-%d')

    tweets = tw.Cursor(api.search,
                        q=search,
                        lang="en",
                        result_type="mixed",
                        since=date_since).items()
    
    results = []
    count = 0

    for tweet in tweets:
        single_tweet = {}
        single_tweet["date"] = str(tweet.created_at)[:10]

        original_text = tweet.text
        processed_text = process_original_tweet(original_text)
        single_tweet["original_text"] = original_text
        single_tweet["processed_text"] = process_original_tweet(processed_text)
        
        blob = TextBlob(processed_text)
        single_tweet["polarity"] = blob.sentiment.polarity
        single_tweet["subjectivity"] = blob.sentiment.subjectivity

        count += 1
        print("current progress for {}: {}".format(company_name, count))

        results.append(single_tweet)

    with open(Path("results/{}-{}.json".format(company_name, date_since)), "w") as output_file:
        json.dump(results, output_file)
    
    return results

def add_current_twitter(company_name, client_address):
    client = MongoClient(client_address)
    db = client.twitter_current
    tweets = scrap_tweets_today(company_name)
    db[company_name].insert_many(tweets)
    client.close()

def generate_blob_sentiment_database(company_name, client_address):
    """
    Calculate the textblob sentiment scores and put them into the database.

    :param company_name: the name of the company. Used as the entry in the database.
    """
    client = MongoClient(client_address)
    db = client.sentrade_db
    twitter_db = client.twitter_current
    sentiment_db = client.sentiment_current

    news_dates = []
    news_scores = []
    today_news_count = 0

    all_date = twitter_db[company_name].distinct("date")

    progress_full = len(all_date)
    progress_count = 0
    for date in all_date:
        news_score = 0  
        news_count = sys.float_info.epsilon
        # sum all scores
        for company_tweet in twitter_db[company_name].find({"date": date}):
            if "polarity" in company_tweet:
                # get rid of the neutral results
                # if company_tweet["polarity"] < -0.3 or company_tweet["polarity"] > 0.3:
                news_score += company_tweet["polarity"]
                news_count += 1
        # check if the date is not yet in the database
        if (sentiment_db[company_name].count_documents({"date": date}) == 0):
            sentiment = {"company": company_name,
                         "date": date,
                         "1_day_sentiment_score": news_score / news_count,
                         "1_day_overall_sentiment_score": news_score,
                         "1_day_news_count": news_count}
            sentiment_db[company_name].insert_one(sentiment)
        else:
            updated_sentiment_score = {"$set": {"1_day_sentiment_score": news_score / news_count,
                                                "1_day_overall_sentiment_score": news_score,
                                                "1_day_news_count": news_count}}
            sentiment_db[company_name].update_one(sentiment_db[company_name].find_one({"date": date}), updated_sentiment_score)
        progress_count += 1
        print("summarise", company_name, "progress:", progress_count, "/", progress_full)
        
    client.close()

if __name__ == "__main__":
    companies = ["apple", "amazon", "facebook", "google", "microsoft", "netflix", "tesla", "uber"]
    client_address = "mongodb://admin:sentrade@45.76.133.175:27017"

    for company in companies:
        # scrap_tweets_today(company)
        add_current_twitter(company, client_address)
        generate_blob_sentiment_database(company, client_address)
