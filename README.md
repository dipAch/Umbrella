# Umbrella
This is a command line utility weather app, that aggregates weather information from multiple weather APIs and analyzes the deviation in their data. It employs python threads to do the fetches in real time.
This program is also a demonstration of the power of threads and how hey can be used for real-time applications as this.

## Usage
To start the program
- ```python weather_forecast.py```
- The program comes with commands for on-screen instructions
- Type ```help``` or ```-h```
- To get the weather forecast, just enter the ```<CITY_NAME>``` and ```<UNIT>```
- The ```<UNIT>``` tends to default to `KELVIN` for OWM and `FAHRENHEIT` for YAHOO
- The weaher APIs will do the rest
- Sit back and relax
- To quit the program, type ```quit``` or ```-q```

## Implementation
- [X] Python
- [X] Python Threading Module
- [X] Python Threading Event

### Code Structure
- The code has been spread out across multiple ```python``` functions in a single file
- The code uses ```TABS```
