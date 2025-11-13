import shutil
import datetime
import os
import glob
import re
import logging
import json
import csv
import subprocess
from logging.handlers import RotatingFileHandler

# Try to import Flask; if it's not available, provide small fallbacks so the script can run.
try:
    from flask import Flask, render_template, jsonify
    USE_FLASK = True
except ImportError:
    Flask = None
    USE_FLASK = False

    # Minimal fallback for render_template so imports succeed; real template rendering is disabled.
    def render_template(template_name, **context):
        # When Flask isn't installed, return a simple placeholder string instead of rendering a template.
        return f"Template rendering not available: {template_name}"

# Try to import requests; if it's not available, provide a flag.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # Provide the import to type-checkers/linters only (not executed at runtime).
    import requests  # type: ignore

try:
    # Import requests dynamically to avoid static analysis errors if the package is not installed,
    # and to make the runtime behavior explicit.
    import importlib
    requests = importlib.import_module('requests')
    USE_REQUESTS = True
except Exception:
    # If requests isn't available or import fails for any reason, fall back gracefully.
    requests = None
    USE_REQUESTS = False

# Note: logger and log_handler are configured later in the file after the handler is created.

if USE_FLASK and Flask is not None:
    app = Flask(__name__, template_folder='.', static_folder='.')
else:
    # Provide a minimal app stub so @app.route decorators are no-ops when Flask is not installed.
    class _DummyApp:
        def __init__(self):
            pass
        def route(self, rule, **options):
            def decorator(f):
                return f
            return decorator
    app = _DummyApp()

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_file = 'app/app.log'
# ensure the log directory exists so RotatingFileHandler can open the file
os.makedirs(os.path.dirname(log_file), exist_ok=True)
log_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=10)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

if USE_FLASK and Flask is not None:
    app = Flask(__name__, template_folder='.', static_folder='.')
else:
    # Re-initialize app if Flask was not available, to ensure it's a _DummyApp
    class _DummyApp:
        def __init__(self):
            pass
        def route(self, rule, **options):
            def decorator(f):
                return f
            return decorator
    app = _DummyApp()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logs')
def get_logs():
    with open(log_file, 'r') as f:
        return jsonify(f.readlines())

# --- Global Variables ---
def get_last_saturday():
    """Finds the date of the last Saturday."""
    today = datetime.date.today()
    # today.weekday(): Monday is 0, Sunday is 6. Saturday is 5.
    days_behind = (today.weekday() - 5 + 7) % 7
    if days_behind == 0:
        days_behind = 7
    target_date = today - datetime.timedelta(days=days_behind)
    return target_date.strftime("%Y-%m-%d")


def get_next_saturday():
    """Finds the date of the next upcoming Saturday."""
    today = datetime.date.today()
    # today.weekday(): Monday is 0, Sunday is 6. Saturday is 5.
    days_ahead = (5 - today.weekday() + 7) % 7
    
    if days_ahead == 0: days_ahead = 7
        
    target_date = today + datetime.timedelta(days=days_ahead)
    return target_date.strftime("%Y-%m-%d") # Formats as "YYYY-MM-DD"


def get_kjv_text(reading):
    """Fetches the KJV text for a given Bible reading."""
    if not USE_REQUESTS:
        logger.error("Requests library not available. Cannot fetch KJV text.")
        return None
    if not reading:
        return None
    
    # Remove "### " from the beginning of the reading
    reading = reading.replace("### ", "")
    
    try:
        response = requests.get(f"https://bible-api.com/{reading}?translation=kjv")
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        verses = data.get('verses')
        if not verses:
            # Fallback or if the 'verses' key is not present
            return data.get('text', '').strip()

        # Process verses to include verse number and text per line
        formatted_text = []
        for verse in verses:
            verse_number = verse.get('verse')
            verse_text = verse.get('text', '').strip()
            formatted_text.append(f"{verse_number} {verse_text}")
            
        return '\n'.join(formatted_text)

    except Exception as e:
        logger.error(f"An error occurred during KJV text fetch: {e}")
        return None

def process_source_directories(date_str):
    """Copies and renames files in all 'doc*' directories."""
    
    script_path = os.path.dirname(os.path.abspath(__file__))
    prayer_breakfast_dir = os.path.dirname(script_path)
    
    source_dirs = glob.glob(os.path.join(prayer_breakfast_dir, 'doc*'))

    def find_source_file(directory):
        for file in os.listdir(directory):
            # Ignore hidden files and the script itself
            if not file.startswith('.') and not file.endswith('.py'):
                return os.path.join(directory, file)
        return None

    tasks = []
    for source_dir in source_dirs:
        source_file = find_source_file(source_dir)
        if source_file:
            # The destination file will be in the same directory as the source file
            dest_file = os.path.join(source_dir, f"{date_str} Saturday Prayer Breakfast Agenda.md")
            tasks.append((source_file, dest_file))

    if not tasks:
        logger.error("Error: Could not find any source files to process.")
        return

    # --- Run the copy operations ---
    try:
        for src, dest in tasks:
            if not os.path.exists(src):
                logger.error(f"Error: Source file not found: {src}")
                continue
            
            # To avoid copying the file over itself if the name is the same
            if src == dest:
                logger.warning(f"Skipping copy as source and destination are the same: {src}")
                continue
            
            if os.path.exists(dest):
                logger.warning(f"Destination file already exists, skipping copy: {dest}")
                continue

            logger.info(f"Copying {src} \n    to {dest}...")
            shutil.copy(src, dest)
            logger.info("Done.\n")
            
        logger.info("All tasks completed successfully.")

    except Exception as e:
        logger.error(f"\nAn error occurred: {e}")


def get_pages_with_readings(prayer_md_content):
    """
    Scans Prayer.md content and returns a list of page numbers
    that contain at least one numbered reading (e.g., "1. ...").
    """
    pages = []
    current_page = None
    for line in prayer_md_content:
        page_match = re.search(r"^## Page (\d+)", line)
        if page_match:
            current_page = int(page_match.group(1))
        
        # Check for lines starting with a number and a period, e.g., "1. " or " 1. "
        reading_match = re.search(r"^\s*\d+\.", line)
        if reading_match and current_page is not None:
            if current_page not in pages:
                pages.append(current_page)
    return pages

def get_reading_line_for_page(page, prayer_md_content):
    """
    Constructs the full reading line for a given page number,
    e.g., "### Page 37 II—STUDYING: 3. Matthew 4:4".
    """
    content_block = ""
    in_page = False
    page_header = f"## Page {page}"
    for line in prayer_md_content:
        # Start capturing when the correct page header is found
        if line.strip() == page_header:
            in_page = True
            continue
        # Stop capturing if we've moved to the next page
        if in_page:
            if line.startswith("## Page"):
                break
            content_block += line

    if not content_block:
        return None

    sub_header = ""
    reading = ""

    for line in content_block.splitlines():
        # Capture the sub-header, e.g., "### II—STUDYING:"
        if line.startswith("### "):
            sub_header = line.strip().replace("### ", "").strip()
            if sub_header.endswith(':'):
                sub_header = sub_header[:-1]
        
        # Capture the first numbered reading line, e.g., "3. Matthew 4:4"
        match = re.search(r"^\s*(\d+\.\s*[^,]+)", line)
        if match:
            reading = match.group(1).strip()
            break  # Use the first numbered reading found on the page

    if not reading:
        return None
    
    # Assemble the final line
    parts = [f"### Page {page}"]
    if sub_header:
        parts.append(sub_header)
    parts.append(reading)
    
    return " ".join(parts)

def get_reading_from_full_line(full_line):
    """Extracts the reading (e.g., 'Matthew 4:4') from a full reading line."""
    if not full_line:
        return None
    # This regex looks for a pattern like "3. Matthew 4:4" and captures "Matthew 4:4"
    match = re.search(r'\d+\.\s*(.*)', full_line)
    if match:
        return match.group(1).strip()
    return None

# --- Procedures to be executed ---
def execute_step_1_title():
    logger.info("Executing Step 1: Process Title")

    """Duplicates files from last_saturday to next_saturday and replaces the date in the title of the agenda files."""
    last_saturday = get_last_saturday()
    next_saturday = get_next_saturday()

    script_path = os.path.dirname(os.path.abspath(__file__))
    prayer_breakfast_dir = os.path.dirname(script_path)

    source_dirs = glob.glob(os.path.join(prayer_breakfast_dir, 'doc*'))

    # --- Duplicate Files ---
    for source_dir in source_dirs:
        source_file_path = os.path.join(source_dir, f"{last_saturday} Saturday Prayer Breakfast Agenda.md")
        dest_file_path = os.path.join(source_dir, f"{next_saturday} Saturday Prayer Breakfast Agenda.md")

        if os.path.exists(source_file_path):
            if not os.path.exists(dest_file_path):
                shutil.copy(source_file_path, dest_file_path)
                logger.info(f"Copied {source_file_path} to {dest_file_path}")
            else:
                logger.warning(f"Destination file already exists, skipping copy: {dest_file_path}")
        else:
            logger.warning(f"Source file not found, skipping copy: {source_file_path}")

    # --- Update Title ---
    for source_dir in source_dirs:
        dest_file_path = os.path.join(source_dir, f"{next_saturday} Saturday Prayer Breakfast Agenda.md")

        if os.path.exists(dest_file_path):
            with open(dest_file_path, 'r') as f:
                content = f.read()

            old_title_line = f"## {last_saturday} Saturday Prayer Breakfast Agenda"
            new_title_line = f"## {next_saturday} Saturday Prayer Breakfast Agenda"

            if old_title_line in content:
                content = content.replace(old_title_line, new_title_line)

                with open(dest_file_path, 'w') as f:
                    f.write(content)
                logger.info(f"Updated title in: {dest_file_path}")
            else:
                logger.warning(f"Title for {last_saturday} not found in {dest_file_path}")
        else:
            logger.warning(f"File not found for title update: {dest_file_path}")

    logger.info("Step 1: Process Title completed.")

def execute_step_2_brr():
    logger.info("Executing Step 2: Bible Reading Rotation")
 
    """Processes the Bible Reading Rotation."""

    def get_reading_for_date(target_date, hq2_content):
        month_str = target_date.strftime("%B").upper()
        day = target_date.day
        
        month_found = False
        for line in hq2_content:
            if line.strip() == f"## **{month_str}**":
                month_found = True
                continue
            
            if month_found and line.startswith('| ' + str(day) + ' '):
                parts = line.split('|')
                if len(parts) > 2:
                    return "### " + parts[2].strip()
        return None

    next_saturday = get_next_saturday()
    last_saturday = get_last_saturday()
    
    next_saturday_date = datetime.datetime.strptime(next_saturday, "%Y-%m-%d").date()
    last_saturday_date = datetime.datetime.strptime(last_saturday, "%Y-%m-%d").date()

    script_path = os.path.dirname(os.path.abspath(__file__))
    prayer_breakfast_dir = os.path.dirname(script_path)
    
    hq2_path = os.path.join(prayer_breakfast_dir, 'app', 'hq2.md')
    if not os.path.exists(hq2_path):
        logger.error(f"Error: hq2.md not found at {hq2_path}")
        return

    with open(hq2_path, 'r') as f:
        hq2_content = f.readlines()

    new_reading = get_reading_for_date(next_saturday_date, hq2_content)
    old_reading = get_reading_for_date(last_saturday_date, hq2_content)

    if not new_reading:
        logger.warning(f"Could not find reading for {next_saturday}")
        return
        
    if not old_reading:
        logger.warning(f"Could not find reading for {last_saturday}")
        # Fallback to finding the reading in the file
        
    source_dirs = glob.glob(os.path.join(prayer_breakfast_dir, 'doc*'))

    for source_dir in source_dirs:
        dest_file_path = os.path.join(source_dir, f"{next_saturday} Saturday Prayer Breakfast Agenda.md")
        if os.path.exists(dest_file_path):
            with open(dest_file_path, 'r') as f:
                content = f.read()

            # If we couldn't find the old reading in HQ2.md, try to find it in the file
            if not old_reading:
                match = re.search(r"###\s.*", content)
                if match:
                    old_reading = match.group(0)

            if old_reading:
                # Use regex to find and replace the old reading
                old_reading_pattern = re.escape(old_reading.strip())
                if re.search(old_reading_pattern, content):
                    content = re.sub(old_reading_pattern, new_reading.strip(), content)
                    with open(dest_file_path, 'w') as f:
                        f.write(content)
                    logger.info(f"Updated Bible Reading in: {dest_file_path} to {new_reading}")
                else:
                    logger.warning(f"Old reading not found in {dest_file_path}")
            else:
                logger.warning(f"Old reading not found in {dest_file_path}")


    # --- Replace KJV text for doc1 ---
    source1_dir = os.path.join(prayer_breakfast_dir, 'doc1')
    source1_file_path = os.path.join(source1_dir, f"{next_saturday} Saturday Prayer Breakfast Agenda.md")

    if os.path.exists(source1_file_path):
        old_reading_text = get_kjv_text(old_reading)
        new_reading_text = get_kjv_text(new_reading)

        """ 
        logger.debug(f"Old Reading Text: {old_reading_text}")
        logger.debug(f"New Reading Text: {new_reading_text}") 
        """    

        if old_reading_text and new_reading_text:
            with open(source1_file_path, 'r') as f:
                content = f.read()

            if old_reading_text in content:
                content = content.replace(old_reading_text, new_reading_text)
                with open(source1_file_path, 'w') as f:
                    f.write(content)
                logger.info(f"Updated KJV text in: {source1_file_path}")
            else:
                logger.warning(f"Old KJV text not found in {source1_file_path}")
    else:
        logger.warning(f"File not found, skipping KJV text replacement: {source1_file_path}")

    logger.info("Step 2: Bible Reading Rotation completed.")

def execute_step_3_pct():
    logger.info("Executing Step 3: Prayer Card Together")

    """Processes the Prayer Card Together section using page numbers."""
    next_saturday = get_next_saturday()

    script_path = os.path.dirname(os.path.abspath(__file__))
    prayer_breakfast_dir = os.path.dirname(script_path)

    prayer_md_path = os.path.join(prayer_breakfast_dir, 'app', 'prayer.md')
    if not os.path.exists(prayer_md_path):
        logger.error(f"Error: prayer.md not found at {prayer_md_path}")
        return

    with open(prayer_md_path, 'r') as f:
        prayer_md_content = f.readlines()

    pages_with_readings = get_pages_with_readings(prayer_md_content)
    if not pages_with_readings:
        logger.error("Error: No pages with numbered readings found in Prayer.md")
        return

    source_dirs = glob.glob(os.path.join(prayer_breakfast_dir, 'doc*'))

    for source_dir in source_dirs:
        dest_file_path = os.path.join(source_dir, f"{next_saturday} Saturday Prayer Breakfast Agenda.md")
        if os.path.exists(dest_file_path):
            with open(dest_file_path, 'r') as f:
                content = f.read()

            # Find the section and extract the current page number
            pct_section_pattern = r"## Prayer Card Together\n### Page (\d+)"
            match = re.search(pct_section_pattern, content)

            if match:
                current_reading_index = int(match.group(1)) # This is the page number
                
                # Find the full line that needs to be replaced
                line_match = re.search(r"(### Page \d+.*)", content)
                if not line_match:
                    logger.warning(f"Could not find full reading line in {dest_file_path}")
                    continue
                old_reading_full_line = line_match.group(1).strip()
                logger.info(f"Found old reading line: {old_reading_full_line}")

                try:
                    current_page_list_index = pages_with_readings.index(current_reading_index)
                    # Find the next page number, looping to the start if necessary
                    next_page_list_index = (current_page_list_index + 1) % len(pages_with_readings)
                    next_reading_index = pages_with_readings[next_page_list_index]
                    
                    # Log the next reading index (page number) as requested
                    logger.info(f"Next reading index (page): {next_reading_index}")

                    new_reading_full_line = get_reading_line_for_page(next_reading_index, prayer_md_content)
                    logger.info(f"Generated new reading line: {new_reading_full_line}")

                    if new_reading_full_line:
                        new_content = content.replace(old_reading_full_line, new_reading_full_line)
                        
                        # --- KJV Text Replacement for doc1 ---
                        if 'doc1' in source_dir:
                            old_reading = get_reading_from_full_line(old_reading_full_line)
                            new_reading = get_reading_from_full_line(new_reading_full_line)

                            if old_reading and new_reading:
                                old_kjv_text = get_kjv_text(old_reading)
                                new_kjv_text = get_kjv_text(new_reading)
                                
                                # logger.debug(f"Old KJV text: {old_kjv_text}")
                                # logger.debug(f"New KJV text: {new_kjv_text}")

                                if old_kjv_text and new_kjv_text and old_kjv_text in new_content:
                                    new_content = new_content.replace(old_kjv_text, new_kjv_text)
                                    logger.info(f"Updated KJV text for Prayer Card Together in: {dest_file_path}")
                                else:
                                    logger.warning(f"Could not replace KJV text in {dest_file_path}. Old text not found or new text not available.")

                        with open(dest_file_path, 'w') as f:
                            f.write(new_content)
                        logger.info(f"Updated Prayer Card Together in: {dest_file_path} from page {current_reading_index} to {next_reading_index}")
                    else:
                        logger.warning(f"Could not generate new reading line for page {next_reading_index}")

                except ValueError:
                    logger.warning(f"Current page number {current_reading_index} not found in the list of pages with readings.")
            else:
                logger.warning(f"\"## Prayer Card Together\" section or page number not found in {dest_file_path}")
        else:
            logger.warning(f"File not found: {dest_file_path}")
            
    logger.info("Step 3: Prayer Card Together completed.")

def execute_step_4_ir():
    logger.info("Executing Step 4: International Reading")

    """Processes the International Reading section."""

    def get_reading_from_hq1(target_date, hq1_content_lines):
        """Extracts reading from hq1.md for a specific day."""
        day = target_date.day
        day_marker = f"## **DAY {day}**"
        day_found = False
        reading_lines = []
        for line in hq1_content_lines:
            if line.strip().startswith(day_marker):
                day_found = True
                continue
            
            if day_found:
                if line.startswith("## **DAY"):
                    break
                reading_lines.append(line.strip())
        
        if reading_lines:
            return " ".join(reading_lines)
        return None

    next_saturday = get_next_saturday()
    next_saturday_date = datetime.datetime.strptime(next_saturday, "%Y-%m-%d").date()

    script_path = os.path.dirname(os.path.abspath(__file__))
    prayer_breakfast_dir = os.path.dirname(script_path)
    
    hq1_path = os.path.join(prayer_breakfast_dir, 'app', 'hq1.md')
    if not os.path.exists(hq1_path):
        logger.error(f"Error: hq1.md not found at {hq1_path}")
        return

    with open(hq1_path, 'r') as f:
        hq1_content_lines = f.readlines()

    new_reading_text = get_reading_from_hq1(next_saturday_date, hq1_content_lines)

    if not new_reading_text:
        logger.warning(f"Could not find reading for DAY {next_saturday_date.day} in HQ1.md")
        return

    # Extract bible reference from the end of the reading
    new_bible_ref_match = re.search(r'((?:\d\s)?[A-Za-z]+(?:\s[A-Za-z]+)*\s\d+:\d+(?:-\d+)?)', new_reading_text)
    new_bible_ref = new_bible_ref_match.group(1).strip() if new_bible_ref_match else None    
    # logger.debug(f"Extract bible reference from the end of the reading: {new_bible_ref}")

    new_reading_main_text = new_reading_text
    if new_bible_ref:
        new_reading_main_text = new_reading_text.replace(new_bible_ref, "").strip()

    source_dirs = glob.glob(os.path.join(prayer_breakfast_dir, 'doc*'))

    for source_dir in source_dirs:
        dest_file_path = os.path.join(source_dir, f"{next_saturday} Saturday Prayer Breakfast Agenda.md")
        if os.path.exists(dest_file_path):
            with open(dest_file_path, 'r') as f:
                content = f.read()

            section_pattern = r"(## International Reading by TaeWoo Lee\n)([\s\S]*?)(?=\n## |\Z)"
            section_match = re.search(section_pattern, content)

            if section_match:
                old_section_content = section_match.group(2)
                
                new_section_content = f"### {new_reading_main_text}\n"
                if new_bible_ref:
                    new_section_content += f"### {new_bible_ref}\n"

                # logger.debug(f"New section content: {new_section_content}")
                
                # new_kjv_text = get_kjv_text(new_bible_ref)
                # logger.debug(f"After this, Processing source1 for new_bible_ref: {new_bible_ref}")


                if 'doc1' in source_dir and new_bible_ref:
                    logger.info(f"Fetching KJV text for {new_bible_ref} for {dest_file_path}")
                    new_kjv_text = get_kjv_text(new_bible_ref)
                    if new_kjv_text:
                        new_section_content += f"{new_kjv_text}\n"
                        logger.info("Added KJV text to International Reading section.")

                new_content = content.replace(old_section_content, new_section_content)

                with open(dest_file_path, 'w') as f:
                    f.write(new_content)
                logger.info(f"Updated International Reading in: {dest_file_path}")
            else:
                logger.warning(f"Could not find 'International Reading' section in {dest_file_path}")

    logger.info("Step 4: International Reading completed.")

def execute_step_5_sr():
    logger.info("Executing Step 5: State Reading")

    """Processes the State Reading section."""

    def get_reading_from_FL(target_date, FL_content_lines):
        """Extracts reading from FL.md for a specific day."""
        day = target_date.day
        day_marker = f"## Day {day}"
        day_found = False
        reading_lines = []
        for line in FL_content_lines:
            if line.strip().startswith(day_marker):
                day_found = True
                continue
            
            if day_found:
                if line.startswith("## Day"):
                    break
                reading_lines.append(line.strip())
        
        if reading_lines:
            return " ".join(reading_lines)
        return None

    next_saturday = get_next_saturday()
    next_saturday_date = datetime.datetime.strptime(next_saturday, "%Y-%m-%d").date()

    script_path = os.path.dirname(os.path.abspath(__file__))
    prayer_breakfast_dir = os.path.dirname(script_path)
    
    FL_path = os.path.join(prayer_breakfast_dir, 'app', 'fl.md')
    if not os.path.exists(FL_path):
        logger.error(f"Error: FL.md not found at {FL_path}")
        return

    # logger.debug(f"FL_path: {FL_path}")
    # logger.debug(f"prayer_breakfast_dir: {prayer_breakfast_dir}")

    with open(FL_path, 'r') as f:
        FL_content_lines = f.readlines()

    new_reading_text = get_reading_from_FL(next_saturday_date, FL_content_lines)

    # logger.debug(f"new_reading_text: {new_reading_text}")
    # logger.debug(f"next_saturday_date.day: {next_saturday_date.day}")
    

    if not new_reading_text:
        logger.error(f"Error FL.md not found at {FL_path}")

    if not new_reading_text:
        logger.warning(f"Could not find reading for DAY {next_saturday_date.day} in fl.md")
        return

    # Extract bible reference from the end of the reading
    new_bible_ref_match = re.search(r'((?:\d\s)?[A-Za-z]+(?:\s[A-Za-z]+)*\s\d+:\d+(?:-\d+)?)', new_reading_text)
    new_bible_ref = new_bible_ref_match.group(1).strip() if new_bible_ref_match else None    
    logger.debug(f"Extract bible reference from the end of the reading: {new_bible_ref}")

    new_reading_main_text = new_reading_text
    if new_bible_ref:
        new_reading_main_text = new_reading_text.replace(new_bible_ref, "").strip()

    source_dirs = glob.glob(os.path.join(prayer_breakfast_dir, 'doc*'))

    for source_dir in source_dirs:
        dest_file_path = os.path.join(source_dir, f"{next_saturday} Saturday Prayer Breakfast Agenda.md")
        if os.path.exists(dest_file_path):
            with open(dest_file_path, 'r') as f:
                content = f.read()

            section_pattern = r"(## State Reading by Alvin Beverly\n)([\s\S]*?)(?=\n## |\Z)"
            section_match = re.search(section_pattern, content)

            if section_match:
                old_section_content = section_match.group(2)
                
                new_section_content = f"### {new_reading_main_text}\n"
                if new_bible_ref:
                    new_section_content += f"### {new_bible_ref}\n"

                logger.debug(f"New section content: {new_section_content}")
                
                new_kjv_text = get_kjv_text(new_bible_ref)
                logger.debug(f"After this, Processing source1 for new_bible_ref: {new_bible_ref}")


                if 'doc1' in source_dir and new_bible_ref:
                    logger.info(f"Fetching KJV text for {new_bible_ref} for {dest_file_path}")
                    new_kjv_text = get_kjv_text(new_bible_ref)
                    if new_kjv_text:
                        new_section_content += f"{new_kjv_text}\n"
                        logger.info("Added KJV text to State Reading section.")

                new_content = content.replace(old_section_content, new_section_content)

                with open(dest_file_path, 'w') as f:
                    f.write(new_content)
                logger.info(f"Updated State Reading in: {dest_file_path}")
            else:
                logger.warning(f"Could not find 'State Reading' section in {dest_file_path}")

    logger.info("Step 5: State Reading completed.")

def execute_step_6_widows():
    logger.info("Executing Step 6: Pray for the Widows")

    """Processes the Widow Reading section."""

    """
    ### 15. Southeast Region – SE12 (cont'd)
    Indian River - Patricia Dodson, Rachel Meeks, 
    Melbourne/Viera - Blanche Lorber, Brenda Ollis, 
    Palm Bay - Harriet Wall, 
    """

    def get_reading_from_W(target_date, W_content_lines):
        """Extracts reading from Widow.md for a specific day."""
        day = target_date.day
        day_marker = f"### {day}."
        
        in_section = False
        reading_lines = []

        for line in W_content_lines:
            if not in_section and line.strip().startswith(day_marker):
                in_section = True

            if in_section:
                if line.startswith("### ") and not line.strip().startswith(day_marker):
                    break
                reading_lines.append(line)

        if reading_lines:
            return "".join(reading_lines).rstrip()
        return None

    next_saturday = get_next_saturday()
    next_saturday_date = datetime.datetime.strptime(next_saturday, "%Y-%m-%d").date()

    script_path = os.path.dirname(os.path.abspath(__file__))
    prayer_breakfast_dir = os.path.dirname(script_path)
    
    W_path = os.path.join(prayer_breakfast_dir, 'app', 'widow.md')
    if not os.path.exists(W_path):
        logger.error(f"Error: widow.md not found at {W_path}")
        return

    # logger.debug(f"W_path: {W_path}")
    # logger.debug(f"prayer_breakfast_dir: {prayer_breakfast_dir}")

    with open(W_path, 'r') as f:
        W_content_lines = f.readlines()

    new_reading_text = get_reading_from_W(next_saturday_date, W_content_lines)

    logger.debug(f"new_reading_text: {new_reading_text}")
    logger.debug(f"next_saturday_date.day: {next_saturday_date.day}")
    

    if not new_reading_text:
        logger.error(f"Error Widow.md not found at {W_path}")
    if not new_reading_text:
        logger.warning(f"Could not find reading for DAY {next_saturday_date.day} in widow.md")
        return

    source_dirs = glob.glob(os.path.join(prayer_breakfast_dir, 'doc*'))

    for source_dir in source_dirs:
        dest_file_path = os.path.join(source_dir, f"{next_saturday} Saturday Prayer Breakfast Agenda.md")
        if os.path.exists(dest_file_path):
            with open(dest_file_path, 'r') as f:
                content = f.read()

            section_pattern = r"(## Widow Reading by Donald Tise\n)([\s\S]*?)(?=\n## |\Z)"
            section_match = re.search(section_pattern, content)

            if section_match:
                old_section_content = section_match.group(2)
                new_section_content = new_reading_text
                
                logger.debug(f"New section content: {new_section_content}")
                
                new_content = content.replace(old_section_content, new_section_content)

                with open(dest_file_path, 'w') as f:
                    f.write(new_content)
                logger.info(f"Updated Widow Reading in: {dest_file_path}")
            else:
                logger.warning(f"Could not find 'Widow Reading' section in {dest_file_path}")

    logger.info("Step 6: Pray for the Widows completed.")

def execute_step_7_pastor():
    logger.info("Executing Step 7: Pray for Local Pastor")
    """Processes the Pray for Local Pastor section."""

    next_saturday = get_next_saturday()

    script_path = os.path.dirname(os.path.abspath(__file__))
    prayer_breakfast_dir = os.path.dirname(script_path)
    
    local_csv_path = os.path.join(prayer_breakfast_dir, 'app', 'local.csv')
    if not os.path.exists(local_csv_path):
        logger.error(f"Error: local.csv not found at {local_csv_path}")
        return

    pastors = []
    with open(local_csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                pastors.append(row[0].strip())

    if not pastors:
        logger.error("Error: No pastors found in local.csv")
        return

    # Find the current pastor in the local.csv file
    current_pastor_name = None
    if pastors:
        current_pastor_name = pastors[0]
    
    if current_pastor_name is None:
        logger.error("Error: Could not find current pastor in local.csv")
        return

    # Find the next pastor
    next_pastor_name = None
    if len(pastors) > 1:
        next_pastor_name = pastors[1]
    else:
        next_pastor_name = pastors[0] # Loop back to the first if only one or none

    if next_pastor_name is None:
        logger.error("Error: No pastors found in local.csv to rotate.")
        return

    # Update local.csv with the next pastor at the top
    updated_pastors = [next_pastor_name] + [p for p in pastors if p != next_pastor_name]
    with open(local_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        for pastor in updated_pastors:
            writer.writerow([pastor])
    logger.info(f"Rotated pastor in local.csv from {current_pastor_name} to {next_pastor_name}")

    # Update the agenda files
    source_dirs = glob.glob(os.path.join(prayer_breakfast_dir, 'doc*'))

    for source_dir in source_dirs:
        dest_file_path = os.path.join(source_dir, f"{next_saturday} Saturday Prayer Breakfast Agenda.md")
        if os.path.exists(dest_file_path):
            with open(dest_file_path, 'r') as f:
                content = f.read()

            section_pattern = r"(## Pray for Local Pastor\n### )(.*)(?=\n## |\Z)"
            section_match = re.search(section_pattern, content)

            if section_match:
                old_pastor_line = section_match.group(2)
                new_pastor_line = next_pastor_name

                new_content = content.replace(old_pastor_line, new_pastor_line)

                with open(dest_file_path, 'w') as f:
                    f.write(new_content)
                logger.info(f"Updated 'Pray for Local Pastor' section in: {dest_file_path} to {next_pastor_name}")
            else:
                logger.warning(f"Could not find 'Pray for Local Pastor' section in {dest_file_path}")
        else:
            logger.warning(f"File not found: {dest_file_path}")

    logger.info("Step 7: Pray for Local Pastor completed.")








if __name__ == '__main__':
    logger.info('Starting the main program execution.')
    
    execute_step_1_title()
    execute_step_2_brr()
    execute_step_3_pct()
    execute_step_4_ir()
    execute_step_5_sr()
    execute_step_6_widows()
    execute_step_7_pastor()
    
    logger.info('All procedures completed.')
    # The Flask app can be run separately if the dashboard is needed.
    app.run(debug=True)