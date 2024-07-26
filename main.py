import requests, re, csv
import pandas as pd
from datetime import datetime


url = "https://www.mrc.gen.mn.us/freq.txt"

def parse_line(line):
    if(line.strip() == ""): return
    columns=line.replace("<-", "").strip().split()

    # find the position of the region code to know how many tokens the city name takes up
    for i, token in enumerate(columns):
        if(len(token)) == 2:
            break

    city = " ".join(columns[0:i])
    region = columns[i]
    output_freq = columns[i+1]
    call_sign = columns[i+2]
    sponsor = columns[i+3]
    ctcss_parts = columns[i+4:-1]
    ctcss_access = ' '.join(ctcss_parts)
    update_date = columns[-1]



    ctcss_access_with_tags = []
    for token in ctcss_access.split(" "):
        if token == "O": token = "Open/Carrier Access"
        elif token == "C": token =  "*Closed Access*"
        elif token == "AP": token = "Autopatch"
        elif token == "CA": token = "Closed Autopatch"
        elif token == "DS": token = "Dual Sequelch"
        elif token == "E": token = "Emergency Power"
        elif token == "WX": token = "Weather Net"
        elif token == "L": token = "Link and/or Crossband"
        elif token == "X": token = "Wide Area Coverage"
        elif token == "LiTZ": token = "Long Tone Zero"
        elif token == "P": token = "Portable"
        elif token == "Z": token = "Autopatch to Law Enforcement"

        ctcss_access_with_tags.append(token)

    ctcss_access_with_tags = " ".join(ctcss_access_with_tags)

    result = {
        "City": city,
        "Region": region,
        "Output": output_freq,
        "Call": call_sign,
        "Sponsor": sponsor,
        "Raw CTCSS Access Info": ctcss_access,
        "CTCSS Access with Tags Replaced": ctcss_access_with_tags,
        "Last Updated Date": update_date
    }

    return result



response = requests.get("https://www.mrc.gen.mn.us/freq.txt")

if response.status_code != 200:
    print(response.text)
    exit(1)


page_data = response.text
page_lines = page_data.split("\n")

matcher = r'.*-- (.*) --.*'

sections = {}
current_section = None

for line in page_lines:
    stripped_line = line.strip()
    just_set = False
    match_result = re.search(matcher, stripped_line)
    if match_result is not None:
        current_section = match_result.group(1).strip()
        just_set = True
    else:
        if current_section != None and not just_set:
            parsed_line = parse_line(stripped_line)
            if parsed_line is not None:
                if current_section in sections:
                    sections[current_section].append(parsed_line)
                else:
                    sections[current_section] = [parsed_line]



# Create a DataFrame from the parsed data
tables = f"""
<h1>Minnesota Repeaters</h1>

<div> 
    <em>Note: This is a parsed version of the following page: <a href="{url}">{url}</a></em>
</div>
<div>
    <em>The parser script was last run on {datetime.now()}</em>
</div>
"""
df_list = []
for section, items in sections.items():
    df = pd.DataFrame(items)

    # Generate an HTML table
    html_table = df.to_html(index=False, escape=False)

    tables += f"<h2>{section}</h2>"
    tables += html_table
    tables += "</br></hr>"

# Write the HTML table to a file (e.g., "radio_stations.html")
with open("docs/index.html", "w") as html_file:
    html_file.write(tables)