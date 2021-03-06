__author__ = "Fengming Liu"
__status__ = "prototype"

import calendar
import os
import pymongo
import sys
import tarfile
import time
from tw_funcs import create_dir, process_bz2_db, download_archive
import subprocess
import urllib3
import shutil

# essential variables
year = 2019
month = "9"
day_start = 1
day_end = 30
time_log_dir = create_dir("./time_log/")
db_client = pymongo.MongoClient(os.environ["CLIENT_ADDR"])
# db_client = pymongo.MongoClient(os.environ["CLIENT_ADDR"])
# db = db_client["temp"]
db = db_client["twitter_data"]
keyword_list = ["netflix", "amazon", "apple", "microsoft", "google", "tesla", "facebook"]
month_abbr_to_num = {name: num for num, name in enumerate(calendar.month_abbr) if num}

# traverse through the days
for day in range(day_start, day_end + 1):
	date = "{0}_{1}_{2}".format(year, str(month).zfill(2), str(day).zfill(2))

	try:
		# download archive zip
		date_tar_filename = "./twitter_stream_{0}.tar".format(date)
		http = urllib3.PoolManager()
		url = "https://ia803103.us.archive.org/7/items/archiveteam-twitter-stream-2019-08/twitter_stream_2019_09_{0}.tar".format(str(day).zfill(2))
		with http.request('GET', url, preload_content=False) as response, open(date_tar_filename, 'wb') as out_file:
			# print(response.status)
			if response.status == 404:
				continue
			else:
				print("Downloading the tar file", date_tar_filename)
				shutil.copyfileobj(response, out_file)
	except:
		print("problem in downloading", date)
		continue

	# extract bz2 files
	date_tar = tarfile.open(date_tar_filename, 'r')
	for mem in date_tar.getmembers():
		# start time
		time_log = open(time_log_dir + "{0}.log".format(date), 'a')
		start_tick = time.time()

		# extract the member out
		if mem.isfile():
			date_tar.extract(mem)
		else:
			continue

		try:
			# unzip the bz2 file to json file
			tw_json_bz2_filename = mem.name
			tw_json_filename = tw_json_bz2_filename.split('.')[0] + ".json"
			process_bz2_db(tw_json_bz2_filename, keyword_list, db, year, month, month_abbr_to_num)
		except:
			print("problem in processing", date)
			continue

		# end time
		end_tick = time.time()
		time_log.write("{0:15s}	{1:.3f}\n".format(tw_json_filename, end_tick - start_tick))
		time_log.close()

	# remove tar file and empty folder
	date_tar.close()
	print("Remove " + date_tar_filename)
	subprocess.run("rm " + date_tar_filename, shell=True)
	print("Remove dirs")
	subprocess.run("rm -r ./{0}".format(str(day).zfill(2)), shell=True)
