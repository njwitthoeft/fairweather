"""Fishing tool."""

import pprint
import re
import requests
from bs4 import BeautifulSoup as BS

# Step 2: Fetch the webpage content
url = "https://www.ndbc.noaa.gov/data/Forecasts/FZAK51.PAFC.html"
response = requests.get(url)
content = response.content

soup = BS(content, "html.parser")

# only section we care about
forecast = soup.find("div", {"class": "fcst"})
report_areas = {
    "Cook Inlet Kalgin Island to Point Bede": "PKZ742-230015",
    "Cook Inlet North of Kalgin Island": "PKZ740-230015",
    "Kachemak Bay": "PKZ741-230015",
}
reports = {k: {} for k in report_areas.keys()}
kids = list(forecast.children)

for idx, child in enumerate(kids):
    cstr = str(child)
    for area in report_areas.keys():
        if area in cstr:
            reports[area]["first_idx"] = idx

keys = list(reports.keys())
reports[keys[0]]["last_idx"] = reports[keys[1]]["first_idx"]
reports[keys[1]]["last_idx"] = reports[keys[2]]["first_idx"]
reports[keys[2]]["last_idx"] = None


for name, report in reports.items():
    print(report)
    print(report["first_idx"])
    report_content = kids[report["first_idx"] : report["last_idx"]]
    report["content"] = report_content

for name, report in reports.items():
    print(report["content"])
# pprint.pprint(reports)
