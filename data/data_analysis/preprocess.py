#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import datetime
import pandas as pd

__author__ = "Fengming Liu"
__status__ = "Development"

def get_relativeday(date):
    rel_days = (date - datetime.date(2019, 1, 1)).days
#    print(type(rel_days))
    return rel_days

def get_num(num_dict):
    if not isinstance(num_dict, dict):
        return None
    if "$numberInt" in num_dict:
        return float(num_dict["$numberInt"])
    elif "$numberDouble" in num_dict:
        return float(num_dict["$numberDouble"])
    else:
        return 0

def get_stock_df(company):
    stock_df = pd.read_json("./stock_price/{0}.json".format(company), lines=True)
    stock_df.insert(loc=0, column="relative_day", value=None)
    for index, row in stock_df.iterrows():
        # stock_df.loc[index, "company"] = company
        stock_df.loc[index, "relative_day"] = get_relativeday(row["date"].date())
        stock_df.loc[index, "open"] = get_num(row["open"])
        stock_df.loc[index, "high"] = get_num(row["high"])
        stock_df.loc[index, "low"] = get_num(row["low"])
        stock_df.loc[index, "close"] = get_num(row["close"])
        stock_df.loc[index, "volume"] = get_num(row["volume"])
        stock_df.loc[index, "change"] = get_num(row["change"])
        stock_df.loc[index, "rise"] = get_num(row["rise"])
        stock_df.loc[index, "change rate"] = get_num(row["change rate"])
        stock_df.loc[index, "label"] = get_num(row["label"])
    stock_df.rename(columns={"label": "up_cat"}, inplace=True)
    stock_df.drop(["_id", "date", "company_name"], axis=1, inplace=True)
    return stock_df

def get_senti_df(company):
    senti_df = pd.read_json("./sentiment_score/{0}.json".format(company), lines=True)
    senti_df.insert(loc=1, column="relative_day", value=None)
    for index, row in senti_df.iterrows():
        senti_df.loc[index, "relative_day"] = get_relativeday(row["date"].date())
        senti_df.loc[index, "today_sentiment_score"] = get_num(row["today_sentiment_score"])
        senti_df.loc[index, "1_day_sentiment_score"] = get_num(row["1_day_sentiment_score"])
        senti_df.loc[index, "3_day_sentiment_score"] = get_num(row["3_day_sentiment_score"])
        senti_df.loc[index, "7_day_sentiment_score"] = get_num(row["7_day_sentiment_score"])
        senti_df.loc[index, "today_news_count"] = get_num(row["today_news_count"])
        senti_df.loc[index, "1_day_news_count"] = get_num(row["1_day_news_count"])
        senti_df.loc[index, "3_day_news_count"] = get_num(row["3_day_news_count"])
        senti_df.loc[index, "7_day_news_count"] = get_num(row["7_day_news_count"])
        senti_df.loc[index, "today_overall_sentiment_score"] = get_num(row["today_overall_sentiment_score"])
        senti_df.loc[index, "1_day_overall_sentiment_score"] = get_num(row["1_day_overall_sentiment_score"])
        senti_df.loc[index, "3_day_overall_sentiment_score"] = get_num(row["3_day_overall_sentiment_score"])
        senti_df.loc[index, "7_day_overall_sentiment_score"] = get_num(row["7_day_overall_sentiment_score"])
        senti_df.loc[index, "today_bert_sentiment_score"] = get_num(row["today_bert_sentiment_score"])
        senti_df.loc[index, "1_day_bert_sentiment_score"] = get_num(row["1_day_bert_sentiment_score"])
        senti_df.loc[index, "3_day_bert_sentiment_score"] = get_num(row["3_day_bert_sentiment_score"])
        senti_df.loc[index, "7_day_bert_sentiment_score"] = get_num(row["7_day_bert_sentiment_score"])
        senti_df.loc[index, "today_overall_bert_sentiment_score"] = get_num(row["today_overall_bert_sentiment_score"])
        senti_df.loc[index, "1_day_overall_bert_sentiment_score"] = get_num(row["1_day_overall_bert_sentiment_score"])
        senti_df.loc[index, "3_day_overall_bert_sentiment_score"] = get_num(row["3_day_overall_bert_sentiment_score"])
        senti_df.loc[index, "7_day_overall_bert_sentiment_score"] = get_num(row["7_day_overall_bert_sentiment_score"])
    senti_df.drop(["_id", "date"], axis=1, inplace=True)
    return senti_df

############################## Main ##############################
total_df = pd.DataFrame()
company_list = ["apple", "amazon", "facebook", "google", 
                "microsoft", "netflix", "tesla", "uber"]

for company in company_list:
    # preprocess stock data
    stock_df = get_stock_df(company)
    
    # preprocess sentiment data
    senti_df = get_senti_df(company)
    
    # merge data
    total_df = total_df.append(pd.merge(stock_df, senti_df, 
                                        on=["relative_day"]), ignore_index=True)

# One hot encoding
total_df = pd.concat([total_df, pd.get_dummies(total_df['company'], 
                                               prefix='company')], axis=1)
total_df.drop(columns=['company'], inplace=True)
# total_df.dropna(inplace=True)
total_df.to_csv("./total_data.csv", index=False)