python3 /Volumes/182TB/BAK/prayer.breakfast/dir/code.py > /Volumes/182TB/BAK/prayer.breakfast/dir/log.txt
crontab /Volumes/182TB/BAK/prayer.breakfast/dir/cronfile.txt
0 9 * * 1 /opt/anaconda3/bin/python3 /Volumes/182TB/BAK/prayer.breakfast/dir/code.py > /Volumes/182TB/BAK/prayer.breakfast/dir/log.txt
rm /Volumes/182TB/BAK/prayer.breakfast/dir/cronfile.txt






# Get today's date
today = datetime.date.today()

# Find the next Saturday
# weekday() returns 0 for Monday and 6 for Sunday. Saturday is 5.
days_to_add = (5 - today.weekday() + 7) % 7
if days_to_add == 0: # If today is Saturday, get next Saturday
    days_to_add = 7

next_saturday = today + datetime.timedelta(days=days_to_add)

# From next_saturday, get just the date portion and format it
day_of_month = next_saturday.day
strHQ1Date = f"## **DAY {day_of_month}**"

# Write into terminal the value of strHQ1Date
# print(strHQ1Date)

# Format the date and store it in strTitle
strTitle = next_saturday.strftime('%Y-%m-%d')

# Combine strTitle with " Saturday Prayer Breakfast Agenda"
strTitle = f"" + strTitle + " Saturday Prayer Breakfast Agenda"


# Write into terminal the value of strTitle
# print(strTitle)

# Read the content of the markdown file
with open('/Volumes/182TB/BAK/prayer.breakfast/HQ1.md', 'r') as f:
    hq1_content = f.read()

# Find the text under the heading
# We can use regex to find the content between two headings.
# The pattern will look for the start heading, capture everything until the next heading or end of file.
pattern = re.compile(f"^{re.escape(strHQ1Date)}(.*?)(?=^## \\*\\*DAY|\\Z)", re.S | re.M)
match = pattern.search(hq1_content)

strHQ1Text = ""
if match:
    strHQ1Text = match.group(1).strip()

# Print the extracted text
# print(strHQ1Text)

# From next_saturday, get just the month portion and format it
month_name = next_saturday.strftime('%B').upper()
strHQ2Month = f"## **{month_name}**"

# Write into terminal the value of strHQ2Month
# print(strHQ2Month)

# Read the content of the markdown file
with open('/Volumes/182TB/BAK/prayer.breakfast/HQ2.md', 'r') as f:
    hq2_content = f.read()

# Find the month section
month_pattern = re.compile(f"^{re.escape(strHQ2Month)}(.*?)(?=^## \\*\\*|\\Z)", re.S | re.M)
month_match = month_pattern.search(hq2_content)

strHQ2Text = ""
if month_match:
    month_section = month_match.group(1)
    
    # Find the row for the specific day
    day_pattern = re.compile(rf"^\|\s*{day_of_month}\s*\|\s*(.*?)\s*\|", re.M)
    day_match = day_pattern.search(month_section)
    
    if day_match:
        strHQ2Text = day_match.group(1).strip()

# Print the extracted text
# print(strHQ2Text)

# From next_saturday, get just the date portion and format it
# day_of_month = next_saturday.day
strWidowsDate = f"### {day_of_month}."

# Write into terminal the value of strHQ1Date
# print(strWidowsDate)

# Read the content of the markdown file

with open('/Volumes/182TB/BAK/prayer.breakfast/Widows.md', 'r') as f:

    widows_content = f.read()



# Find the line that starts with strWidowDate

strWidowsTitle = ""

for line in widows_content.splitlines():

    if line.lower().startswith(strWidowsDate.lower()):

        strWidowsTitle = line

        break



# Print the extracted title

# print(strWidowsTitle)



# Find the text under the title

# We can use regex to find the content between two headings.

# The pattern will look for the start heading, capture everything until the next heading or end of file.

pattern = re.compile(f"^{re.escape(strWidowsTitle)}(.*?)(?=^###|---)", re.S | re.M)
match = pattern.search(widows_content)



strWidowsText = ""
if match:

    strWidowsText = match.group(1).strip()



# Process the extracted text
locations = {}
for line in strWidowsText.splitlines():
    if not line.strip():
        continue
    # remove "- " prefix
    line = line.strip()[2:]
    parts = line.split(',')
    name = parts[0].strip()
    location = ','.join(parts[1:]).strip()
    if location not in locations:
        locations[location] = []
    locations[location].append(name)

# Format the output string
formatted_lines = []
for location, names in locations.items():
    formatted_lines.append(f"{location} - {', '.join(names)},")

strWidowsText = "\n".join(formatted_lines)

# Print the final formatted text
# print(strWidowsText)



# From next_saturday, get just the date portion and format it
day_of_month = next_saturday.day
strFLDate = f"## Day {day_of_month}"

# Write into terminal the value of strFLDate
# print("Current strFLDate:", strFLDate)

# Read the content of the markdown file

with open('/Volumes/182TB/BAK/prayer.breakfast/FL.md', 'r') as f:

    fl_content = f.read()

# Find the text under the heading
# Updated pattern to match "## Day X" with optional additional text, handling empty lines
pattern = re.compile(f"^## Day {day_of_month}[^\n]*\n\n(.*?)(?=\n##|\n---)", re.S | re.M)
match = pattern.search(fl_content)

strFLText = ""
if match:
    strFLText = match.group(1).strip()

# Print the extracted text
# print("Current strFLText:", repr(strFLText))

# Find the last Saturday (or today if it is Saturday)
days_to_subtract = (today.weekday() - 5 + 7) % 7
last_saturday = today - datetime.timedelta(days=days_to_subtract)

# Read the content of the markdown file from last Saturday
file_path_last = f"/Volumes/182TB/BAK/prayer.breakfast/{last_saturday.strftime('%Y-%m-%d')} Saturday Prayer Breakfast Agenda.md"
with open(file_path_last, 'r') as f:
    last_content = f.read()

# Create the new file path for next Saturday
new_file_path = f"/Volumes/182TB/BAK/prayer.breakfast/{next_saturday.strftime('%Y-%m-%d')} Saturday Prayer Breakfast Agenda.md"

# Write the content to the new file
with open(new_file_path, 'w') as f:
    f.write(last_content)

# print(f"Copied content from {file_path_last} to {new_file_path}")

# Define the titles to be replaced
strLastTitle = f"## {last_saturday.strftime('%Y-%m-%d')} Saturday Prayer Breakfast Agenda"
strNextTitle = f"## {next_saturday.strftime('%Y-%m-%d')} Saturday Prayer Breakfast Agenda"

# Read the content of the new file
with open(new_file_path, 'r') as f:
    new_content = f.read()

# Replace the title
new_content = new_content.replace(strLastTitle, strNextTitle)

# Find and extract the line below "- Prayer Card Together" and store it in strPrayerCardNo
prayer_card_marker = "- Prayer Card Together"
prayer_card_index = new_content.find(prayer_card_marker)
if prayer_card_index != -1:
    # Find the next line after the marker
    next_line_start = new_content.find('\n', prayer_card_index) + 1
    next_line_end = new_content.find('\n', next_line_start)
    if next_line_end == -1:  # If it's the last line
        full_line = new_content[next_line_start:].strip()
    else:
        full_line = new_content[next_line_start:next_line_end].strip()
    
    # Extract just the number from the line (e.g., "### 36 - Praying" -> "36")
    import re
    number_match = re.search(r'(\d+)', full_line)
    if number_match:
        strPrayerCardNo = number_match.group(1)
    else:
        strPrayerCardNo = ""
else:
    strPrayerCardNo = ""

# Increment the prayer card number for next week
if strPrayerCardNo.isdigit():
    next_prayer_card_no = str(int(strPrayerCardNo) + 1)
else:
    next_prayer_card_no = "1"  # Default to 1 if no valid number found

# Print the extracted and incremented prayer card numbers for testing
# print("Current strPrayerCardNo:", repr(strPrayerCardNo))
# print("Next prayer card number:", repr(next_prayer_card_no))


# Find and replace text between "- Bible Reading Rotation" and "- Prayer Card Together"
bible_reading_marker = "- Bible Reading Rotation"

start_index = new_content.find(bible_reading_marker)
end_index = new_content.find(prayer_card_marker)

if start_index != -1 and end_index != -1:
    replacement_text = f"{bible_reading_marker}\n{strHQ2Text}\n\n{prayer_card_marker}"
    new_content = new_content[:start_index] + replacement_text + new_content[end_index + len(prayer_card_marker):]

# Find and replace text between "- International Reading by TaeWoo Lee" and "- State Reading by Alvin Beverly"
international_reading_marker = "- International Reading by TaeWoo Lee"
state_reading_marker = "- State Reading by Alvin Beverly"

start_index = new_content.find(international_reading_marker)
end_index = new_content.find(state_reading_marker)

if start_index != -1 and end_index != -1:
    end_of_first_line = new_content.find('\n', start_index)
    replacement_text = f"{international_reading_marker}\n{strHQ1Text}\n\n{state_reading_marker}"
    new_content = new_content[:start_index] + replacement_text + new_content[end_index + len(state_reading_marker):]

# Find and replace text between "- Pray for the Widows by Donald Tise" and "- Pray for Local Pastor by Johnny Perry"
widows_marker = "- Pray for the Widows by Donald Tise"
local_pastor_marker = "- Pray for Local Pastor by Johnny Perry"

start_index = new_content.find(widows_marker)
end_index = new_content.find(local_pastor_marker)

if start_index != -1 and end_index != -1:
    replacement_text = f"{widows_marker}\n{strWidowsTitle}\n{strWidowsText}\n\n{local_pastor_marker}"
    new_content = new_content[:start_index] + replacement_text + new_content[end_index + len(local_pastor_marker):]

# Find and replace text between "- State Reading by Alvin Beverly" and "- Pray for the Widows by Donald Tise"
state_reading_marker = "- State Reading by Alvin Beverly"

start_index = new_content.find(state_reading_marker)
end_index = new_content.find(widows_marker)

if start_index != -1 and end_index != -1:
    replacement_text = f"{state_reading_marker}\n{strFLDate}\n{strFLText}\n\n{widows_marker}"
    new_content = new_content[:start_index] + replacement_text + new_content[end_index + len(widows_marker):]

# Find the line that says "- Pray for Local Pastor by Johnny Perry"
# Store the line below it as strChurchText
# Store the line below strChurchText as strPastorText
local_pastor_index = new_content.find(local_pastor_marker)
if local_pastor_index != -1:
    lines_after_marker = new_content[local_pastor_index:].splitlines()
    if len(lines_after_marker) > 1:
        strChurchText = lines_after_marker[1]
    else:
        strChurchText = ""
    if len(lines_after_marker) > 2:
        strPastorText = lines_after_marker[2]
    else:
        strPastorText = ""



# print(f"{strChurchText}")  
# print(f"{strPastorText}")

# Read the content of the CSV file
file_path_csv = f"/Volumes/182TB/BAK/prayer.breakfast/local.csv"
with open(file_path_csv, 'r') as f:
    csv_content = f.read()

# Parse CSV and find the row matching strPastorText and strChurchText, then get the next row
reader = csv.reader(csv_content.splitlines())
rows = list(reader)

strNewPastorText = ""
strNewChurchText = ""

# Clean up strChurchText and strPastorText to extract actual values
# strChurchText is like "### New Life Word Center Church"
# strPastorText is like "### Lady Patricia Merthie"
church_name = strChurchText.replace("###", "").strip()
pastor_name = strPastorText.replace("###", "").strip()

# Find the matching row
for i, row in enumerate(rows):
    if len(row) > 10:
        # Check if church name matches (column 10)
        if church_name in row[10]:
            # Check if pastor name matches (columns 7, 8, 9 for title, first, last)
            full_name = f"{row[7]} {row[8]} {row[9]}".strip()
            if pastor_name in full_name or full_name in pastor_name:
                # Found the matching row, get the next row
                if i + 1 < len(rows):
                    next_row = rows[i + 1]
                    if len(next_row) > 10:
                        strNewChurchText = f"### {next_row[10]}"
                        strNewPastorText = f"### {next_row[7]} {next_row[8]} {next_row[9]}"
                break

# Find and replace the two lines between "- Pray for Local Pastor by Johnny Perry" and "- Prayer Request"
prayer_request_marker = "- Prayer Request"

local_pastor_index = new_content.find(local_pastor_marker)
prayer_request_index = new_content.find(prayer_request_marker)

if local_pastor_index != -1 and prayer_request_index != -1:
    # Find the start of the line after local_pastor_marker
    start_line_index = new_content.find('\n', local_pastor_index) + 1
    # Find the start of prayer_request_marker line
    end_line_index = prayer_request_index
    
    # Replace the content between them
    replacement_text = f"{strNewChurchText}\n{strNewPastorText}\n\n"
    new_content = new_content[:start_line_index] + replacement_text + new_content[end_line_index:]

# (f"{strNewChurchText}")
# print(f"{strNewPastorText}")

# print(f"{new_content}")

# Read the content of the markdown file for Prayer Card
file_path_prayer = f"/Volumes/182TB/BAK/prayer.breakfast/Prayer.md"
with open(file_path_prayer, 'r') as f:
    prayer_content = f.read()

# Find the line that matches "## Page {next_prayer_card_no}" pattern
page_pattern = f"## Page {next_prayer_card_no}"
page_match_line = ""

# Search for the line in prayer_content
for line in prayer_content.split('\n'):
    if line.strip() == page_pattern:
        page_match_line = line.strip()
        break

# Print the found line for testing
# print("Found page line:", repr(page_match_line))








# print(f"{new_content}")

# Write the updated content back to the file
with open(new_file_path, 'w') as f:
    f.write(new_content)

# print(f"Updated title in {new_file_path}")

# Convert the new markdown file to DOCX using pandoc (requires pandoc installed)
docx_file_path = new_file_path.replace(".md", ".docx")
try:
    subprocess.run(["pandoc", new_file_path, "-o", docx_file_path], check=True)
    print(f"Converted {new_file_path} to {docx_file_path} using pandoc")
except FileNotFoundError:
    print("pandoc not found; please install pandoc (https://pandoc.org/) to enable markdown->docx conversion")
except subprocess.CalledProcessError as e:
    print(f"pandoc conversion failed: {e}")


# Convert the new markdown file to PDF using pandoc
""" pdf_file_path = new_file_path.replace(".md", ".pdf")
try:
    subprocess.run(["pandoc", new_file_path, "-o", pdf_file_path, "--pdf-engine=weasyprint", "--metadata", f"title={strTitle}"], check=True)
    print(f"Converted {new_file_path} to {pdf_file_path} using pandoc")
except FileNotFoundError:
    print("pandoc not found; please install pandoc (https://pandoc.org/) to enable markdown->pdf conversion")
except subprocess.CalledProcessError as e:
    print(f"pandoc conversion failed: {e}") """

# Print Essential

# Detail

# Print Detail

# Email Chaplain


