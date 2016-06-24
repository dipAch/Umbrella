#!/usr/bin/python

# @tweeting_dipa
# All imports here
import threading
import json
import time
import sys
import urllib2, urllib

####### GLOBALS Section #######

# SHELL ENV
SHELL_ICON = ">>> "

# Shell commands
HELP = "help"
HYPHEN_HELP = "-h"
SHOW = "show"
WEATHER = "weather"
QUIT = "quit"
Q = "-q"

# Utility globals
EMPTY = ""
SPACE = " "

# Asynchronous flow variables
owm_data = {}
yhoo_data = {}
NOTIFICATIONS = ["IDLE...\n", "Fetching...\n", "Processing...\n"]
STATUS = 0
RUNNING = False
TRIGGERED = False

# Program Error (In case of a Runtime Exception or Program Crash)
RUNTIME_ERR = False

# Weather specific
PASCAL = SPACE + "Pa"
CELSIUS = SPACE + "C"
FAHRENHEIT = SPACE + "F"
KELVIN = SPACE + "K"

####### GLOBALS Section #######

##### Utility Section #####

def display_at_boot():
	# On boot, welcome user to CLI app
	print "\n--- Weather App *** v0.1 ---"
	print "### Environment: Python 2.7.3 ###"
	print "--- Type help or -h for on-screen instructions ---\n"

def on_help_call():
	# Show help
	# print "--Usage: To change shell icon -> shell -ch <CHARACTER>"
	print "--Usage: weather <CITY_NAME> [<UNIT [metric | imperial]>]"
	print "--Usage: [-q | quit] to Quit"
	print "--Usage: After running a fetch. Track your fetch using 'show'\n"

def unsupported_cmd():
	# Well people tend to give unsupported commands
	# Either by mistake or some out of pure fun
	# High-Five if you are the second kind
	global RUNTIME_ERR
	if RUNTIME_ERR:
		# If a Runtime Exception occurs, then the message changes by a bit
		# Run the app and let it fail, and you will understand
		print "...I fell while running...It's OK, i'm back up...\n"
		RUNTIME_ERR = False
	else:
	    # For unsupported commands
	    print "...Unsupported Command Type...\n"

##### Utility Section #####

##### Command Processor Engine #####
def process_cmd(cmd):
	'''
	This piece of code / block runs your command line interface
	and the commands that you push into it
	It listens for new commands and checks if a particular
	command is supported by it
	A.K.A, The visible interface of the program
	'''
	# import globals
	global TRIGGERED, RUNNING
	# Sanitize command
	cmd = cmd.lower()
	cmd = cmd.strip()

	# Determine command intent
	if cmd == HELP or cmd == HYPHEN_HELP:
		# Help was invoked
		on_help_call()
	elif cmd == QUIT or cmd == Q:
		# Quit from program
		sys.exit()
	elif cmd == SHOW:
		if TRIGGERED:
			if not check_status():
				print "############ Fetched Data (OWM) ############"
				for key, value in owm_data.iteritems():
					print "%s: %s" % (key, value)
				print
				print "############ Fetched Data (YAHOO) ############"
				for key, value in yhoo_data.iteritems():
					print "%s: %s" % (key, value)
				print
				if not owm_data.get('error', False) and not yhoo_data.get('error', False):
					# Get the difference between the two sources of weather information
					# namely, `OWM` and `YAHOO` weather API
					get_info_difference(owm_data, yhoo_data)
				# Set `TRIGGERED` to `False` to mark command or transaction completion
				TRIGGERED = False
			else:
				print NOTIFICATIONS[STATUS]
		else:
			print "Run a fetch first...Currently nothing to show..."
			print "Currently in %s" % NOTIFICATIONS[STATUS]
	elif not cmd == EMPTY and cmd not in [HELP, HYPHEN_HELP, QUIT, Q, SHOW] and cmd[:7] == WEATHER:
		cmd = cmd[7:].strip()
		if cmd:
		    if not TRIGGERED:
			    # Get OWM data
			    global city, units
			    city, units = get_params(cmd)

			    # Get to running
			    RUNNING = True
			    TRIGGERED = True

			    # Use event signaling to synchronize the threads
			    signal_event = threading.Event()

			    # Spawn OWM API thread
			    owm_th = threading.Thread(target=owm_fetch, name="OWM", args=(signal_event,))
			    owm_th.start()

			    # Spawn Yahoo weather API thread
			    yahoo_th = threading.Thread(target=yahoo_fetch, name="YAHOO", args=(signal_event,))
			    yahoo_th.start()

			    print "--USAGE: Type -> show [For viewing the progress]\n"
		    else:
			    print "Already a fetch is in progress...Please wait for it to finish...\n"
		else:
			# If arguments to the `WEATHER` command is not provided
			# Time for a Refresher
			print "...CMD_INVOKE_ERR: Argument(s) to `WEATHER` missing..."
			on_help_call()
	else:
		# Command was Shit**
		unsupported_cmd()

# Check running status
def check_status():
	return RUNNING

# Do the OWM fetch
def owm_fetch(evnt):
	'''
	The `OWM` weather API in action
	Fetches weather data from the API endpoint
	Unfortunately, you need an API key to use the API since
	December 2015, it was token-free otherwise
	'''
	global owm_data, STATUS, RUNNING, RUNTIME_ERR, TRIGGERED
	try:
		OWM_URI = "http://api.openweathermap.org/data/2.5/weather?q=%s&units=%s&APPID=%s" % (city, units, '<YOUR_OWM_APP_ID>')
		STATUS = 1 # Fetching
		owm_resp = urllib2.urlopen(OWM_URI)
		time.sleep(30)
		owm_json_py = json.loads(owm_resp.read())
		STATUS = 2 # Processing
		time.sleep(30)
		if owm_json_py["cod"] == 200:
			if units == "metric":
				DEGREE = CELSIUS
			elif units == "imperial":
				DEGREE = FAHRENHEIT
			else:
				DEGREE = KELVIN # Default is `KELVIN`
			owm_data = dict(weather_desc=owm_json_py["weather"][0]["description"].title(), pressure=str(owm_json_py["main"]["pressure"]) + PASCAL,
				temp_min=(str(owm_json_py["main"]["temp_min"]) + DEGREE), temp_max=(str(owm_json_py["main"]["temp_max"]) + DEGREE),
				avg_temp=(str(owm_json_py["main"]["temp"]) + DEGREE), humidity=owm_json_py["main"]["humidity"],
				country=owm_json_py["sys"]["country"], location=owm_json_py["name"])
		elif owm_json_py["cod"] == 404:
			owm_data = dict(error=True, message=owm_json_py["message"])
	except Exception as run_tym_excp:
		print 'ERR_OCCURED:(DURING_EXECUTION):OWM_THREAD:', str(run_tym_excp)
		print 'Press <ENTER> to continue. Diagnostics is checking in the background on what went wrong...'
		# Notifies a Runtime Exception Occured
		RUNTIME_ERR = True
		# After a crash, the `COMMAND` fails so TRIGGERED needs to be reset
		TRIGGERED = False
	finally:
		evnt.wait() # Wait for sibling `YAHOO` thread to finish
		RUNNING = False
		STATUS = 0 # Back to idle

# Do the YAHOO fetch
def yahoo_fetch(evnt):
	'''
	The `YAHOO` weather API in action
	Fetches weather data from the API endpoint
	'''
	global yhoo_data, STATUS, RUNNING, RUNTIME_ERR, TRIGGERED
	try:
		YAHOO_URI = "https://query.yahooapis.com/v1/public/yql?"
		yql_query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='%s')" % city
		yql_url = YAHOO_URI + urllib.urlencode({'q': yql_query}) + "&format=json"
		STATUS = 1 # Fetching
		yhoo_resp = urllib2.urlopen(yql_url)
		time.sleep(30)
		yhoo_json_py = json.loads(yhoo_resp.read())
		STATUS = 2 # Processing
		time.sleep(30)
		if yhoo_json_py["query"]["results"] is not None:
			forecast = yhoo_json_py["query"]["results"]["channel"]["item"]["forecast"]
			temp_high = float(forecast[0]["high"])
			temp_low = float(forecast[0]["low"])
			temp_avg = float(yhoo_json_py["query"]["results"]["channel"]["item"]["condition"]["temp"])
			if units == "metric":
				DEGREE = CELSIUS
				temp_high, temp_low, temp_avg = convert_f_to_c(temp_high, temp_low, temp_avg)
			else:
				DEGREE = FAHRENHEIT # Default is Imperial
			yhoo_data = dict(weather_desc=yhoo_json_py["query"]["results"]["channel"]["item"]["condition"]["text"].title(),
				pressure=str(yhoo_json_py["query"]["results"]["channel"]["atmosphere"]["pressure"]) + PASCAL,
				temp_min=(str('%0.2f' % temp_low) + DEGREE), temp_max=(str('%0.2f' % temp_high) + DEGREE),
				avg_temp=(str('%0.2f' % temp_avg) + DEGREE), humidity=yhoo_json_py["query"]["results"]["channel"]["atmosphere"]["humidity"],
				country=yhoo_json_py["query"]["results"]["channel"]["location"]["country"],
				location=yhoo_json_py["query"]["results"]["channel"]["location"]["city"])
		else:
			yhoo_data = dict(error=True, message="Request Failed with 404")
	except Exception as run_tym_excp:
		print 'ERR_OCCURED:(DURING_EXECUTION):YHOO_THREAD:', str(run_tym_excp)
		print 'Press <ENTER> to continue. Diagnostics is checking in the background on what went wrong...'
		# Notifies a Runtime Exception Occured
		RUNTIME_ERR = True
		# After a crash, the `COMMAND` fails so TRIGGERED needs to be reset
		TRIGGERED = False
	evnt.set() # Notify `YAHOO` Finish

# Convert temperature from Fahrenheit to Celsius 
def convert_f_to_c(*temps):
	'''
	Finally using the conversion formula somewhere
	This function is taught as an introduction to CS (atleast where I studied)
	But never quite figured out, if is actually used in the real-world
	Well here it is. The stage is all yours...
	'''
	# Final list of converted temperature values
	converted = []
	for temp in temps:
		temp = (float(temp) - 32) * 5 / 9.0
		converted.append(temp)
	return converted

# Convert temperature from Kelvin to Fahrenheit 
def convert_k_to_f(*temps):
	'''
	The same feeling as above...
	'''
	# Final list of converted temperature values
	converted = []
	for temp in temps:
		temp = temp * 9 / 5.0 - 459.67
		converted.append(temp)
	return converted

# Split command params
def get_params(cmd):
	'''
	This function returns the command parameters
	for our command processor to execute them
	Command parameters: `CITY` and `UNITS`
	'''
	space_count = cmd.count(" ")
	if space_count > 1:
		return cmd.replace(SPACE * space_count, SPACE).split(SPACE)
	elif space_count == 1:
		return cmd.split(SPACE)
	return cmd, EMPTY

# Calculate the difference between the two
# sources of weather information
def get_info_difference(owm_data, yhoo_data):
	'''
	This function only has side-effects
	It shows the difference in the weather report
	from the two weather data sources (`OWM` and `YAHOO`)
	'''
	# Split the `C` or `F` or `K`
	# There's a catch here, can anyone find it?
	# I'm feeling too lazy to do that now
	# I'll correct it at some later point in time
	# It looks and runs well for now
	# Hint: When `OWM` data is in `K` & `YHOO` data is in `F` (The default `UNITS` case!!!)
	# OK. I did it myself!! I'm a perfectionist with no deadline...LOL
	owm_max, yhoo_max = float(owm_data["temp_max"].split()[0]), float(yhoo_data["temp_max"].split()[0])
	owm_avg, yhoo_avg = float(owm_data["avg_temp"].split()[0]), float(yhoo_data["avg_temp"].split()[0])
	owm_min, yhoo_min = float(owm_data["temp_min"].split()[0]), float(yhoo_data["temp_min"].split()[0])
	print "############ Information Difference Data (OWM vs YAHOO) ############"
	# If `OWM` temperature data is in `K` format, need to convert it to `F`
	# We can pick any of the three `OWM` temperature fields and check their `UNIT`
	# I picked the `MAX_TEMP` attribute
	if owm_data["temp_max"].split()[1] == 'K':
		owm_max, owm_avg, owm_min = convert_k_to_f(owm_max, owm_avg, owm_min)
		print '* Making adjustments [Changed `OWM` unit from `Kelvin` to `Fahrenheit`]'
	print '* Difference [Maximum Temperature]:', '%0.2f' % abs(owm_max - yhoo_max)
	print '* Difference [Average Temperature]:', '%0.2f' % abs(owm_avg - yhoo_avg)
	print '* Difference [Minimum Temperature]:', '%0.2f' % abs(owm_min - yhoo_min)
	print

##### Main Section #####
def main():
	# Run welcome
	display_at_boot()

	# Start console process
	while True:
		process_cmd(raw_input(SHELL_ICON))

# Entry point if not loaded as a
# Python Module but as a standalone
# pragmmatic python program. LOL!!!
if __name__ == "__main__":
	main()