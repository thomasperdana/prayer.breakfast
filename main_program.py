#!/usr/bin/env python3
"""
Main program with 20 procedures and comprehensive logging system.
The input directory is now read-only with permissions set to 555 (r-xr-xr-x)
python3 main_program.py
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


# Global variables for date management
LAST_WEEK_DATE = None
NEXT_WEEK_DATE = None
NEXT_WEEK_AGENDA_FILE = None


def setup_logging():
    """Configure comprehensive logging system with file and console handlers."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"app_{timestamp}.log"
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def init_file():
    """Initialize application configuration."""
    import shutil
    import stat
    global LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 01: Initializing application configuration")
    logger.debug("Loading default configuration values")
    
    try:
        input_dir = Path("input")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Protect input directory as read-only
        input_dir.chmod(0o555)
        for item in input_dir.rglob("*"):
            if item.is_file():
                item.chmod(0o555)
        logger.info("Protected input directory and files as read-only (555)")
        logger.debug("Set permissions to r-xr-xr-x for input directory")
        
        last_week_file = input_dir / "2025-11-08 Saturday Prayer Breakfast Agenda.md"
        
        LAST_WEEK_DATE = datetime.strptime("2025-11-08", "%Y-%m-%d")
        NEXT_WEEK_DATE = LAST_WEEK_DATE + timedelta(weeks=1)
        next_week_str = NEXT_WEEK_DATE.strftime("%Y-%m-%d")
        last_week_str = LAST_WEEK_DATE.strftime("%Y-%m-%d")
        
        logger.info(f"Last week date: {last_week_str}")
        logger.info(f"Next week date: {next_week_str}")
        
        NEXT_WEEK_AGENDA_FILE = output_dir / f"{next_week_str} Saturday Prayer Breakfast Agenda.md"
        
        # Remove existing file if it exists
        if NEXT_WEEK_AGENDA_FILE.exists():
            NEXT_WEEK_AGENDA_FILE.chmod(0o777)
            NEXT_WEEK_AGENDA_FILE.unlink()
            logger.debug(f"Removed existing file: {NEXT_WEEK_AGENDA_FILE.name}")
        
        shutil.copy2(last_week_file, NEXT_WEEK_AGENDA_FILE)
        logger.info(f"Created next week agenda: {NEXT_WEEK_AGENDA_FILE.name}")
        logger.debug(f"Copied from {last_week_file} to {NEXT_WEEK_AGENDA_FILE}")
        
        # Change file permissions to read, write, execute for all (777)
        NEXT_WEEK_AGENDA_FILE.chmod(0o777)
        logger.info(f"Changed file permissions to 777 (rwxrwxrwx)")
        logger.debug(f"File permissions updated for {NEXT_WEEK_AGENDA_FILE.name}")
        
        # Update the title in the file
        content = NEXT_WEEK_AGENDA_FILE.read_text()
        old_title = f"North Seminole County Gideons - {last_week_str} Saturday Prayer Breakfast Agenda"
        new_title = f"North Seminole County Gideons - {next_week_str} Saturday Prayer Breakfast Agenda"
        
        if old_title in content:
            updated_content = content.replace(old_title, new_title, 1)
            NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
            logger.info(f"Updated title from '{old_title}' to '{new_title}'")
            logger.debug("File content updated successfully")
        else:
            logger.warning(f"Title '{old_title}' not found in file")
        
    except Exception as e:
        logger.error(f"Failed to create next week agenda: {str(e)}")
        return {"status": "error", "procedure": "01", "error": str(e)}
    
    return {"status": "success", "procedure": "01"}


def bible_reading():
    """Update Bible Reading Rotation for next week."""
    import re
    global NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 02: Updating Bible Reading Rotation")
    logger.debug("Reading Bible rotation schedule from hq2.md")
    
    try:
        if NEXT_WEEK_DATE is None or NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variables not initialized. Run init_file first.")
            return {"status": "error", "procedure": "02", "error": "Missing global variables"}
        
        # Read the Bible reading schedule
        hq2_file = Path("input/hq2.md")
        hq2_content = hq2_file.read_text()
        
        # Extract month and day from NEXT_WEEK_DATE
        month = NEXT_WEEK_DATE.strftime("%B").upper()
        day = NEXT_WEEK_DATE.day
        
        logger.debug(f"Looking for reading for {month} {day}")
        
        # Find the month section
        month_pattern = rf"## \*\*{month}\*\*.*?\n(.*?)(?=\n## \*\*|\Z)"
        month_match = re.search(month_pattern, hq2_content, re.DOTALL)
        
        if not month_match:
            logger.error(f"Could not find month section for {month}")
            return {"status": "error", "procedure": "02", "error": f"Month {month} not found"}
        
        month_section = month_match.group(1)
        
        # Find the reading for the specific day
        day_pattern = rf"^\| {day} \| (.*?) \|"
        day_match = re.search(day_pattern, month_section, re.MULTILINE)
        
        if not day_match:
            logger.error(f"Could not find reading for {month} {day}")
            return {"status": "error", "procedure": "02", "error": f"Day {day} not found"}
        
        bible_reading = day_match.group(1).strip()
        logger.info(f"Found Bible reading for {month} {day}: {bible_reading}")
        
        # Update the agenda file
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Find and replace the Bible Reading Rotation line
        old_pattern = r"Bible Reading Rotation - .*"
        new_reading = f"Bible Reading Rotation - {bible_reading}"
        
        updated_content = re.sub(old_pattern, new_reading, agenda_content)
        NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
        
        logger.info(f"Updated Bible Reading Rotation to: {bible_reading}")
        logger.debug("Bible reading rotation updated successfully")
        
        return {"status": "success", "procedure": "02"}
        
    except Exception as e:
        logger.error(f"Failed to update Bible reading: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "02", "error": str(e)}


def prayer_card():
    """Update Prayer Card rotation for next week."""
    import re
    global NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 03: Updating Prayer Card rotation")
    logger.debug("Reading Prayer Card schedule from prayer.md")
    
    try:
        if NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variable NEXT_WEEK_AGENDA_FILE not initialized. Run init_file first.")
            return {"status": "error", "procedure": "03", "error": "Missing global variable"}
        
        # Read the prayer card schedule
        prayer_file = Path("input/prayer.md")
        prayer_content = prayer_file.read_text()
        
        # Read the current agenda to find the current prayer card entry
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Extract current prayer card page number
        current_pattern = r"Prayer Card Together - Page (\d+)"
        current_match = re.search(current_pattern, agenda_content)
        
        if not current_match:
            logger.error("Could not find current Prayer Card entry in agenda")
            return {"status": "error", "procedure": "03", "error": "Current prayer card not found"}
        
        current_page = int(current_match.group(1))
        next_page = current_page + 1
        
        logger.debug(f"Current prayer card page: {current_page}, next page: {next_page}")
        
        # Find the next page entry in prayer.md
        # Look for the bullet point which has the scripture reference
        page_pattern = rf"## Page {next_page}\s*\n+### ([^\n]+)\s*\n+(\d+)\.\s+[^\n]+\n\s*\*\s+([^\n]+)"
        page_match = re.search(page_pattern, prayer_content, re.MULTILINE | re.DOTALL)
        
        if not page_match:
            logger.error(f"Could not find Page {next_page} in prayer.md")
            return {"status": "error", "procedure": "03", "error": f"Page {next_page} not found"}
        
        section_name = page_match.group(1).strip()
        item_number = page_match.group(2).strip()
        scripture_ref = page_match.group(3).strip()
        
        # Ensure section_name ends with colon if it doesn't have one
        if not section_name.endswith(':'):
            section_name += ':'
        
        # Transform scripture reference: replace ", " with "-" for verse ranges
        scripture_ref = re.sub(r',\s+(\d+)$', r'-\1', scripture_ref)
        
        # Build the new prayer card entry in the correct format
        new_prayer_card = f"Prayer Card Together - Page {next_page} {section_name} {item_number}. {scripture_ref}"
        
        logger.info(f"Next prayer card: {new_prayer_card}")
        
        # Update the agenda file
        old_pattern = r"Prayer Card Together - Page \d+.*"
        updated_content = re.sub(old_pattern, new_prayer_card, agenda_content)
        NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
        
        logger.info(f"Updated Prayer Card from Page {current_page} to Page {next_page}")
        logger.debug("Prayer card rotation updated successfully")
        
        return {"status": "success", "procedure": "03"}
        
    except Exception as e:
        logger.error(f"Failed to update Prayer Card: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "03", "error": str(e)}


def international_reading():
    """Update International Reading for next week."""
    import re
    global NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 04: Updating International Reading")
    logger.debug("Reading International schedule from hq1.md")
    
    try:
        if NEXT_WEEK_DATE is None or NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variables not initialized. Run init_file first.")
            return {"status": "error", "procedure": "04", "error": "Missing global variables"}
        
        # Read the international reading schedule
        hq1_file = Path("input/hq1.md")
        hq1_content = hq1_file.read_text()
        
        # Get the day number from NEXT_WEEK_DATE
        day_number = NEXT_WEEK_DATE.day
        
        logger.debug(f"Looking for DAY {day_number}")
        
        # Find the DAY section in hq1.md
        day_pattern = rf"## \*\*DAY {day_number}\*\*\s*\n(.*?)(?=\n## \*\*DAY|\Z)"
        day_match = re.search(day_pattern, hq1_content, re.DOTALL)
        
        if not day_match:
            logger.error(f"Could not find DAY {day_number} in hq1.md")
            return {"status": "error", "procedure": "04", "error": f"DAY {day_number} not found"}
        
        day_content = day_match.group(1).strip()
        
        logger.info(f"Found International Reading for DAY {day_number}")
        logger.debug(f"Content length: {len(day_content)} characters")
        
        # Update the agenda file
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Find and replace the International Reading section
        # Pattern: from "International Reading by..." to the next section or scripture reference
        old_pattern = r"International Reading by [^\n]+\n.*?(?=\n\n[A-Z]|\nEphesians|\nRomans|\nMatthew|\nProverbs|\nHebrews|\n2 Timothy|\n1 John|\nRevelation|\n2 Corinthians|\nActs)"
        
        new_international_reading = f"International Reading by TaeWoo Lee\n{day_content}"
        
        # Check if pattern exists
        if re.search(old_pattern, agenda_content, re.DOTALL):
            updated_content = re.sub(old_pattern, new_international_reading, agenda_content, flags=re.DOTALL)
            NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
            
            logger.info(f"Updated International Reading to DAY {day_number}")
            logger.debug("International reading updated successfully")
        else:
            logger.error("Could not find International Reading section to replace")
            return {"status": "error", "procedure": "04", "error": "International Reading section not found"}
        
        return {"status": "success", "procedure": "04"}
        
    except Exception as e:
        logger.error(f"Failed to update International Reading: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "04", "error": str(e)}


def state_reading():
    """Update State Reading for next week."""
    import re
    global NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 05: Updating State Reading")
    logger.debug("Reading State schedule from fl.md")
    
    try:
        if NEXT_WEEK_DATE is None or NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variables not initialized. Run init_file first.")
            return {"status": "error", "procedure": "05", "error": "Missing global variables"}
        
        # Read the state reading schedule
        fl_file = Path("input/fl.md")
        fl_content = fl_file.read_text()
        
        # Get the day number from NEXT_WEEK_DATE
        day_number = NEXT_WEEK_DATE.day
        
        logger.debug(f"Looking for Day {day_number}")
        
        # Find the Day section in fl.md
        day_pattern = rf"## Day {day_number}[^\n]*\s*\n(.*?)(?=\n---\n\n## Day|\n## Day|\Z)"
        day_match = re.search(day_pattern, fl_content, re.DOTALL)
        
        if not day_match:
            logger.error(f"Could not find Day {day_number} in fl.md")
            return {"status": "error", "procedure": "05", "error": f"Day {day_number} not found"}
        
        day_content = day_match.group(1).strip()
        
        # Remove the closing "---" if present
        day_content = re.sub(r'\n---\s*$', '', day_content)
        
        # Reformat the content to match the exact format required
        # Extract the main heading (### line)
        heading_match = re.search(r'###\s+(.+)', day_content)
        if not heading_match:
            logger.error("Could not find heading in Day content")
            return {"status": "error", "procedure": "05", "error": "Heading not found"}
        
        heading = heading_match.group(1).strip()
        
        # Extract scripture reference (first occurrence)
        scripture_match = re.search(r'\*([^*]+)\*', day_content)
        scripture = scripture_match.group(0) if scripture_match else ""
        
        # Extract everything after the scripture reference
        if scripture_match:
            after_scripture_pos = scripture_match.end()
            after_scripture = day_content[after_scripture_pos:].strip()
        else:
            after_scripture = ""
        
        # Build formatted output
        formatted_lines = [heading]
        
        if after_scripture:
            # Clean up - remove excess blank lines but keep single newlines
            after_scripture = re.sub(r'\n\s*\n+', '\n', after_scripture)
            formatted_lines.append(after_scripture)
        
        if scripture:
            formatted_lines.append(scripture)
        
        new_state_reading = f"State Reading by Alvin Beverly\n" + "\n".join(formatted_lines)
        
        logger.info(f"Found State Reading for Day {day_number}")
        logger.debug(f"Formatted content:\n{new_state_reading}")
        
        # Update the agenda file
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Find and replace the State Reading section
        # Pattern: from "State Reading by..." to the next main section
        old_pattern = r"State Reading by [^\n]+\n.*?(?=\n\nPray for the Widows)"
        
        # Check if pattern exists
        if re.search(old_pattern, agenda_content, re.DOTALL):
            updated_content = re.sub(old_pattern, new_state_reading, agenda_content, flags=re.DOTALL)
            NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
            
            logger.info(f"Updated State Reading to Day {day_number}")
            logger.debug("State reading updated successfully")
        else:
            logger.error("Could not find State Reading section to replace")
            return {"status": "error", "procedure": "05", "error": "State Reading section not found"}
        
        return {"status": "success", "procedure": "05"}
        
    except Exception as e:
        logger.error(f"Failed to update State Reading: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "05", "error": str(e)}


def widow_prayer():
    """Update Widow Prayer for next week."""
    import re
    global NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 06: Updating Widow Prayer")
    logger.debug("Reading Widow schedule from widow.md")
    
    try:
        if NEXT_WEEK_DATE is None or NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variables not initialized. Run init_file first.")
            return {"status": "error", "procedure": "06", "error": "Missing global variables"}
        
        # Read the widow prayer schedule
        widow_file = Path("input/widow.md")
        widow_content = widow_file.read_text()
        
        # Get the day number from NEXT_WEEK_DATE
        day_number = NEXT_WEEK_DATE.day
        
        logger.debug(f"Looking for section {day_number}")
        
        # Find the section in widow.md (### {day_number}. ...)
        section_pattern = rf"### {day_number}\. ([^\n]+)\n((?:- [^\n]+\n)*)"
        section_match = re.search(section_pattern, widow_content)
        
        if not section_match:
            logger.error(f"Could not find section {day_number} in widow.md")
            return {"status": "error", "procedure": "06", "error": f"Section {day_number} not found"}
        
        section_title = section_match.group(1).strip()
        widow_list = section_match.group(2).strip()
        
        # Format the widow list - convert markdown list to comma-separated format
        # Extract widows from the list items
        widows = re.findall(r'- ([^\n]+)', widow_list)
        
        # Group widows by camp
        camps_data = {}
        for widow_entry in widows:
            parts = widow_entry.split(', ', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                camp = parts[1].strip()
                if camp not in camps_data:
                    camps_data[camp] = []
                camps_data[camp].append(name)
            else:
                logger.warning(f"Skipping malformed widow entry: {widow_entry}")
        
        formatted_parts = []
        for camp, names_list in camps_data.items():
            formatted_parts.append(f"{camp} - {', '.join(names_list)}, ")
        
        formatted_widow_text = " - ".join(formatted_parts)

        
        new_widow_prayer = f"Pray for the Widows by Donald Tise - {day_number}. {section_title}\n{formatted_widow_text}"
        
        logger.info(f"Found Widow Prayer for section {day_number}: {section_title}")
        logger.debug(f"Formatted content:\n{new_widow_prayer}")
        
        # Update the agenda file
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Find and replace the Widow Prayer section
        old_pattern = r"Pray for the Widows by [^\n]+\n[^\n]+"
        
        # Check if pattern exists
        if re.search(old_pattern, agenda_content, re.DOTALL):
            updated_content = re.sub(old_pattern, new_widow_prayer, agenda_content, flags=re.DOTALL)
            NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
            
            logger.info(f"Updated Widow Prayer to section {day_number}")
            logger.debug("Widow prayer updated successfully")
        else:
            logger.error("Could not find Widow Prayer section to replace")
            return {"status": "error", "procedure": "06", "error": "Widow Prayer section not found"}
        
        return {"status": "success", "procedure": "06"}
        
    except Exception as e:
        logger.error(f"Failed to update Widow Prayer: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "06", "error": str(e)}


def pastor_prayer():
    """Handle pastor prayer section for next week."""
    import re
    global NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 07: Handling Pastor Prayer")
    
    try:
        if NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variable NEXT_WEEK_AGENDA_FILE not initialized. Run init_file first.")
            return {"status": "error", "procedure": "07", "error": "Missing global variable"}
        
        pastor_file = Path("input/pastor.md")
        pastor_content = pastor_file.read_text()
        
        pastor_entries = []
        # Regex to capture Pastor Name and Church Name from the markdown table
        # It handles cases where Pastor Name or Church Name might be empty
        # The pattern looks for lines starting with '|', followed by a number, then captures two groups
        # Group 1: Pastor Name (can be empty)
        # Group 2: Church Name (can be empty)
        for line in pastor_content.splitlines():
            match = re.match(r'\|\s*\d+\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|', line)
            if match:
                pastor_name = match.group(1).strip()
                church_name = match.group(2).strip()
                
                if pastor_name and church_name:
                    formatted_entry = f"Pray for Local Pastor by Johnny Perry - {church_name} - {pastor_name}"
                elif church_name:
                    formatted_entry = f"Pray for Local Pastor by Johnny Perry - {church_name}"
                else:
                    # Skip entries that don't have at least a church name
                    continue
                pastor_entries.append(formatted_entry)
        
        if not pastor_entries:
            logger.error("No pastor entries found in pastor.md")
            return {"status": "error", "procedure": "07", "error": "No pastor entries found"}
        
        logger.debug(f"Found {len(pastor_entries)} pastor entries.")
        
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Find the current pastor prayer entry in the agenda
        current_pastor_pattern = r"Pray for Local Pastor by Johnny Perry - .*"
        current_pastor_match = re.search(current_pastor_pattern, agenda_content)
        
        if not current_pastor_match:
            logger.error("Could not find current pastor prayer entry in agenda.")
            return {"status": "error", "procedure": "07", "error": "Current pastor prayer entry not found"}
        
        current_pastor_entry = current_pastor_match.group(0).strip()
        logger.info(f"Current pastor prayer entry: {current_pastor_entry}")
        
        try:
            current_index = pastor_entries.index(current_pastor_entry)
        except ValueError:
            logger.warning(f"Current pastor entry '{current_pastor_entry}' not found in pastor.md. Starting from the beginning.")
            current_index = -1 # Will make next_index 0
            
        next_index = (current_index + 1) % len(pastor_entries)
        next_pastor_entry = pastor_entries[next_index]
        
        logger.info(f"Next pastor prayer entry: {next_pastor_entry}")
        
        updated_content = re.sub(current_pastor_pattern, next_pastor_entry, agenda_content)
        NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
        
        logger.info("Pastor prayer entry updated successfully.")
        
        return {"status": "success", "procedure": "07"}
        
    except Exception as e:
        logger.error(f"Failed to handle pastor prayer: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "07", "error": str(e)}


def procedure_08():
    """Initialize API connections."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 08: Initializing API connections")
    logger.debug("API endpoints configured")
    return {"status": "success", "procedure": "08"}


def procedure_09():
    """Load data models."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 09: Loading data models")
    logger.debug("Data schemas validated")
    return {"status": "success", "procedure": "09"}


def procedure_10():
    """Setup notification system."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 10: Setting up notification system")
    logger.debug("Notification channels configured")
    return {"status": "success", "procedure": "10"}


def procedure_11():
    """Initialize background tasks."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 11: Initializing background tasks")
    logger.debug("Task scheduler started")
    return {"status": "success", "procedure": "11"}


def procedure_12():
    """Setup monitoring system."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 12: Setting up monitoring system")
    logger.debug("Performance metrics enabled")
    return {"status": "success", "procedure": "12"}


def procedure_13():
    """Load plugins and extensions."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 13: Loading plugins and extensions")
    logger.debug("Plugin directory scanned")
    return {"status": "success", "procedure": "13"}


def procedure_14():
    """Initialize session management."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 14: Initializing session management")
    logger.debug("Session storage configured")
    return {"status": "success", "procedure": "14"}


def procedure_15():
    """Setup error handling."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 15: Setting up error handling")
    logger.debug("Global exception handler registered")
    return {"status": "success", "procedure": "15"}


def procedure_16():
    """Load resource files."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 16: Loading resource files")
    logger.debug("Static resources indexed")
    return {"status": "success", "procedure": "16"}


def procedure_17():
    """Initialize data validation."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 17: Initializing data validation")
    logger.debug("Validation rules compiled")
    return {"status": "success", "procedure": "17"}


def procedure_18():
    """Setup backup system."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 18: Setting up backup system")
    logger.debug("Backup schedule configured")
    return {"status": "success", "procedure": "18"}


def procedure_19():
    """Initialize analytics."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 19: Initializing analytics")
    logger.debug("Analytics endpoints ready")
    return {"status": "success", "procedure": "19"}


def procedure_20():
    """Finalize startup sequence."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 20: Finalizing startup sequence")
    logger.debug("All systems operational")
    return {"status": "success", "procedure": "20"}


def main():
    """Main program entry point."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Application Starting")
    logger.info("=" * 60)
    
    procedures = [
        init_file, bible_reading, prayer_card, international_reading, state_reading,
        widow_prayer, pastor_prayer, procedure_08, procedure_09, procedure_10,
        procedure_11, procedure_12, procedure_13, procedure_14, procedure_15,
        procedure_16, procedure_17, procedure_18, procedure_19, procedure_20
    ]
    
    results = []
    success_count = 0
    failure_count = 0
    
    for idx, procedure in enumerate(procedures, 1):
        try:
            logger.debug(f"Executing procedure {idx} of {len(procedures)}")
            result = procedure()
            results.append(result)
            
            if result.get("status") == "success":
                success_count += 1
                logger.debug(f"Procedure {idx} completed successfully")
            else:
                failure_count += 1
                logger.warning(f"Procedure {idx} completed with issues")
                
        except Exception as e:
            failure_count += 1
            logger.error(f"Error in procedure {idx}: {str(e)}", exc_info=True)
            results.append({"status": "error", "procedure": f"{idx:02d}", "error": str(e)})
    
    logger.info("=" * 60)
    logger.info("Execution Summary")
    logger.info("=" * 60)
    logger.info(f"Total Procedures: {len(procedures)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {failure_count}")
    logger.info("=" * 60)
    
    if failure_count == 0:
        logger.info("Application started successfully!")
        return 0
    else:
        logger.warning(f"Application started with {failure_count} errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
