import logging
import random
import re
import shutil
import os
from datetime import datetime, timedelta

# --- Configuration ---
INPUT_DIR = "input"
OUTPUT_DIR = "output"


def setup_logging():
    """Sets up basic logging for the script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def duplicate_file(output_dir):
    """Duplicates last Saturday's agenda to create next Saturday's agenda."""
    logging.info("Step 2a: Duplicating file from last Saturday to next Saturday.")

    today = datetime.now()
    
    # Calculate last Saturday's date
    if today.weekday() == 5:  # Saturday
        last_saturday_date = today - timedelta(days=7)
    else:
        days_since_saturday = (today.weekday() - 5 + 7) % 7
        last_saturday_date = today - timedelta(days=days_since_saturday)

    # Calculate next Saturday's date
    days_until_saturday = (5 - today.weekday() + 7) % 7
    next_saturday_date = today + timedelta(days=days_until_saturday)

    last_saturday_str = last_saturday_date.strftime("%Y-%m-%d")

    source_filename = f"{last_saturday_str} Saturday Prayer Breakfast Agenda.md"
    source_filepath = os.path.join(output_dir, source_filename)

    if not os.path.exists(source_filepath):
        logging.error(f"Source file not found: {source_filepath}")
        return None

    next_saturday_str = next_saturday_date.strftime("%Y-%m-%d")
    new_filename = f"{next_saturday_str} Saturday Prayer Breakfast Agenda.md"
    new_filepath = os.path.join(output_dir, new_filename)

    shutil.copy(source_filepath, new_filepath)
    logging.info(f"File duplicated from {source_filepath} to {new_filepath}")
    return new_filepath

def rename_title(filepath):
    """Renames the title in the markdown file based on the new file's date."""
    logging.info("Step 2b: Renaming title.")
    
    # Extract date from the new filepath
    filename = os.path.basename(filepath)
    # Expected format: "YYYY-MM-DD Saturday Prayer Breakfast Agenda.md"
    date_part = filename.split(" ")[0] # "YYYY-MM-DD"
    
    new_title_line = f"## {date_part} Saturday Prayer Breakfast Agenda"
    
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Assuming the agenda title is the second line
    if len(lines) > 1:
        lines[1] = new_title_line + "\n"
    else:
        logging.warning(f"File {filepath} has less than two lines, cannot rename agenda title.")
        # If there's only one line, append the new title
        lines.append(new_title_line + "\n")
    
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    logging.info(f"Title renamed to: {new_title_line}")

def bible_reading(filepath):
    """Replaces the Bible Reading Rotation section with the reading for the next Saturday."""
    logging.info("Step 2c: Updating bible reading for the next Saturday.")
    
    today = datetime.now()
    days_until_saturday = (5 - today.weekday() + 7) % 7
    next_saturday_date = today + timedelta(days=days_until_saturday)
    
    month_name = next_saturday_date.strftime("%B").upper()
    day_of_month = next_saturday_date.day

    hq2_path = os.path.join(INPUT_DIR, "hq2.md")
    if not os.path.exists(hq2_path):
        logging.error(f"hq2.md not found: {hq2_path}")
        return

    bible_verse = "Bible reading not found for next Saturday."
    try:
        with open(hq2_path, 'r') as f:
            content = f.read()
            
            month_pattern = re.compile(rf"## \*\*({month_name})\*\*(.*?)(?=## \*\*|\Z)", re.DOTALL)
            month_match = month_pattern.search(content)
            
            if month_match:
                month_content = month_match.group(2)
                day_pattern = re.compile(rf"\|\s*{day_of_month}\s*\|\s*(.*?)\s*\|")
                day_match = day_pattern.search(month_content)
                if day_match:
                    bible_verse = day_match.group(1).strip()
    except Exception as e:
        logging.error(f"Error reading or parsing hq2.md: {e}")

    try:
        with open(filepath, 'r') as f:
            agenda_content = f.read()

        # Replace the content under "## Bible Reading Rotation"
        new_agenda_content = re.sub(
            r"(## Bible Reading Rotation\s*\n### ).*?(\n)",
            rf"\1{bible_verse}\2",
            agenda_content,
            flags=re.DOTALL
        )

        with open(filepath, 'w') as f:
            f.write(new_agenda_content)
        logging.info(f"Updated Bible Reading Rotation to: {bible_verse}")
    except Exception as e:
        logging.error(f"Error updating Bible Reading Rotation in agenda file: {e}")

def prayer_card(filepath):
    """Updates the prayer card section by selecting the next item from prayer.md."""
    logging.info("Step 2d: Updating prayer card.")

    prayer_md_path = os.path.join(INPUT_DIR, "prayer.md")
    if not os.path.exists(prayer_md_path):
        logging.error(f"prayer.md not found: {prayer_md_path}")
        return

    try:
        with open(prayer_md_path, 'r') as f:
            prayer_md_content = f.read()
        
        # Split by "## Page" and create a list of entries
        prayer_card_entries = re.split(r'\n## ', prayer_md_content)
        prayer_card_entries = prayer_card_entries[1:]

        if not prayer_card_entries:
            logging.warning("No prayer card entries found in prayer.md.")
            return

        with open(filepath, 'r') as f:
            agenda_content = f.read()

        # Find the current prayer card in the agenda
        current_prayer_card_match = re.search(r"## Prayer Card Together\n### Page (\d+)", agenda_content)
        
        if not current_prayer_card_match:
            logging.warning("Could not find current prayer card in agenda. Using the first entry.")
            next_prayer_card_index = 0
        else:
            current_page_number = current_prayer_card_match.group(1)
            
            current_index = -1
            for i, entry in enumerate(prayer_card_entries):
                if entry.strip().startswith(f"Page {current_page_number}"):
                    current_index = i
                    break
            
            if current_index == -1:
                logging.warning(f"Could not find page {current_page_number} in prayer.md. Using the first entry.")
                next_prayer_card_index = 0
            else:
                next_prayer_card_index = (current_index + 1) % len(prayer_card_entries)

        # Get the next prayer card
        next_entry_raw = prayer_card_entries[next_prayer_card_index]
        
        # Extract the page number
        next_page_match = re.match(r"Page (\d+)", next_entry_raw)
        next_page_number = next_page_match.group(1) if next_page_match else ""

        # Extract the title (e.g., "II—STUDYING:")
        title_match = re.search(r"### (.*?)\n", next_entry_raw)
        title = title_match.group(1).strip() if title_match else ""

        # Extract the reference line (e.g., "4. II Timothy 3:16, 17")
        reference_match = re.search(r"(\d+\.\s+.*?)(?=, \")", next_entry_raw)
        reference = reference_match.group(1).strip() if reference_match else ""

        final_prayer_card_line = f"### Page {next_page_number} {title} {reference}"

        # Replace the old prayer card with the new one
        new_agenda_content = re.sub(
            r"(## Prayer Card Together\n)(### .*?\n)",
            rf"\1{final_prayer_card_line}\n",
            agenda_content,
        )

        with open(filepath, 'w') as f:
            f.write(new_agenda_content)
        
        logging.info(f"Updated prayer card to: {final_prayer_card_line}")

    except Exception as e:
        logging.error(f"Error updating prayer card: {e}")

def international_reading(filepath):
    """Adds an international reading from hq1.md."""
    logging.info("Step 2e: Adding international reading.")
    
    today = datetime.now()
    day_of_month = today.day

    hq1_path = os.path.join(INPUT_DIR, "hq1.md")
    if not os.path.exists(hq1_path):
        logging.error(f"hq1.md not found: {hq1_path}")
        return

    international_content = "International reading not found for today."
    try:
        with open(hq1_path, 'r') as f:
            content = f.read()
            
            # Find the section for the current day
            day_pattern = re.compile(rf"## \*\*DAY {day_of_month}\*\*(.*?)(?=## \*\*DAY |\Z)", re.DOTALL)
            day_match = day_pattern.search(content)
            
            if day_match:
                international_content = day_match.group(1).strip()
    except Exception as e:
        logging.error(f"Error reading or parsing hq1.md: {e}")
        
    # Append to the agenda file
    try:
        with open(filepath, 'a') as f:
            f.write(f"\n## International Reading\n")
            f.write(f"{international_content}\n")
        logging.info(f"Added International reading for Day {day_of_month}.")
    except Exception as e:
        logging.error(f"Error writing International reading to agenda file: {e}")

def state_reading(filepath):
    """Adds a state reading from fl.md."""
    logging.info("Step 2f: Adding state reading.")
    
    today = datetime.now()
    day_of_month = today.day

    fl_path = os.path.join(INPUT_DIR, "fl.md")
    if not os.path.exists(fl_path):
        logging.error(f"fl.md not found: {fl_path}")
        return

    state_content = "State reading not found for today."
    try:
        with open(fl_path, 'r') as f:
            content = f.read()
            
            # Find the section for the current day, including its content
            full_day_pattern = re.compile(rf"(## Day {day_of_month} - .*?)(?=## Day |\Z)", re.DOTALL)
            full_day_match = full_day_pattern.search(content)
            
            if full_day_match:
                state_content = full_day_match.group(1).strip()
            else:
                state_content = "State reading not found for today."

    except Exception as e:
        logging.error(f"Error reading or parsing fl.md: {e}")
        
    # Append to the agenda file
    try:
        with open(filepath, 'a') as f:
            f.write(f"\n## State Reading\n")
            f.write(f"{state_content}\n")
        logging.info(f"Added State reading for Day {day_of_month}.")
    except Exception as e:
        logging.error(f"Error writing State reading to agenda file: {e}")

def widow_prayer(filepath):
    """Adds a widow prayer from widow.md."""
    logging.info("Step 2g: Adding widow prayer.")
    
    widow_path = os.path.join(INPUT_DIR, "widow.md")
    if not os.path.exists(widow_path):
        logging.error(f"widow.md not found: {widow_path}")
        return

    widow_content = "Widow prayer content not found."
    try:
        with open(widow_path, 'r') as f:
            widow_content = f.read().strip()
    except Exception as e:
        logging.error(f"Error reading widow.md: {e}")
        
    # Append to the agenda file
    try:
        with open(filepath, 'a') as f:
            f.write(f"\n## Widow Prayer Calendar\n")
            f.write(f"{widow_content}\n")
        logging.info("Added Widow Prayer Calendar content.")
    except Exception as e:
        logging.error(f"Error writing Widow Prayer Calendar to agenda file: {e}")

def pastor_prayer(filepath):
    """Adds a pastor prayer from pastor.md."""
    logging.info("Step 2h: Adding pastor prayer.")
    
    pastor_path = os.path.join(INPUT_DIR, "pastor.md")
    if not os.path.exists(pastor_path):
        logging.error(f"pastor.md not found: {pastor_path}")
        return

    pastor_content = "Pastor prayer content not found."
    try:
        with open(pastor_path, 'r') as f:
            pastor_content = f.read().strip()
    except Exception as e:
        logging.error(f"Error reading pastor.md: {e}")
        
    # Append to the agenda file
    try:
        with open(filepath, 'a') as f:
            f.write(f"\n## Pastor Directory for Prayer\n")
            f.write(f"{pastor_content}\n")
        logging.info("Added Pastor Directory for Prayer content.")
    except Exception as e:
        logging.error(f"Error writing Pastor Directory to agenda file: {e}")

# Try to import the 'markdown' library; if not available, provide a minimal fallback converter.
try:
    import markdown  # type: ignore
except Exception:
    import html as _html
    import re as _re

    class _MinimalMarkdown:
        @staticmethod
        def markdown(text):
            """Very small markdown-to-HTML fallback: handle headings, bold, italics and paragraphs."""
            if text is None:
                return ""
            # Escape HTML to avoid injecting raw HTML from the markdown source
            out = _html.escape(text)

            # Convert ATX headings: lines starting with 1-6 '#'
            def _repl_heading(m):
                level = len(m.group(1))
                content = m.group(2).strip()
                return f"<h{level}>{content}</h{level}>"
            out = _re.sub(r'^(#{1,6})\s+(.*)$', _repl_heading, out, flags=_re.MULTILINE)

            # Bold: **text**
            out = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', out)

            # Italic: *text*
            out = _re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', out)

            # Simple unordered lists: lines starting with '- ' or '* '
            def _repl_list(match):
                items = [f"<li>{item.strip()}</li>" for item in match.group(0).splitlines()]
                return "<ul>\n" + "\n".join(items) + "\n</ul>"
            out = _re.sub(r'(^[-\*]\s+.+(\n[-\*]\s+.+)+)', _repl_list, out, flags=_re.MULTILINE)

            # Convert remaining double newlines into paragraphs
            paragraphs = [p.strip() for p in out.split('\n\n') if p.strip()]
            paragraphs = [p.replace('\n', '<br/>') for p in paragraphs]
            return '\n\n'.join(f"<p>{p}</p>" for p in paragraphs)

    markdown = _MinimalMarkdown()

def convert_file_to_html(filepath):
    """Converts a markdown file to HTML."""
    logging.info("Step 2i & 2l: Converting file to HTML.")
    
    if not os.path.exists(filepath):
        logging.error(f"Markdown file not found for conversion: {filepath}")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        html_content = markdown.markdown(markdown_content)
        
        html_filepath = filepath.replace(".md", ".html")
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info(f"Converted {filepath} to {html_filepath}")
        return html_filepath
    except Exception as e:
        logging.error(f"Error converting markdown to HTML: {e}")
        return None

def print_file(filepath):
    """'Prints' a file (saves it or displays content)."""
    logging.info("Step 2j & 2m: 'Printing' file.")
    
    if not os.path.exists(filepath):
        logging.error(f"File not found for printing: {filepath}")
        return

    logging.info(f"File ready for review/printing: {filepath}")

def get_scripture(filepath):
    """Gets a scripture and adds it to the file."""
    logging.info("Step 2k: Getting scripture.")
    
    prayer_md_path = os.path.join(INPUT_DIR, "prayer.md")
    if not os.path.exists(prayer_md_path):
        logging.error(f"prayer.md not found: {prayer_md_path}")
        return

    scriptures = []
    try:
        with open(prayer_md_path, 'r') as f:
            content = f.read()
            # Regex to find scripture references like "Romans 1:16" or "II Corinthians 5:17"
            # This pattern looks for common book names, chapter:verse, and handles Roman numerals.
            # It also captures the full line where the scripture is mentioned.
            scripture_pattern = re.compile(r"(\*?\s*[IVXLCDM]*\s*[A-Za-z]+\s+\d+:\d+(?:-\d+)?(?:,\s*\d+)?(?:,\s*\d+:\d+(?:-\d+)?)?\s*\*?)")
            
            # Find all matches
            for line in content.splitlines():
                match = scripture_pattern.search(line)
                if match:
                    # Clean up the matched scripture string
                    scripture_ref = match.group(1).replace('*', '').strip()
                    if scripture_ref: # Ensure it's not an empty string
                        scriptures.append(scripture_ref)

    except Exception as e:
        logging.error(f"Error reading or parsing prayer.md for scriptures: {e}")
        
    selected_scripture = "No scripture found."
    if scriptures:
        selected_scripture = random.choice(scriptures)
        
    # Append to the agenda file
    try:
        with open(filepath, 'a') as f:
            f.write(f"\n## Random Scripture for Reflection\n")
            f.write(f"{selected_scripture}\n")
        logging.info(f"Added random scripture: {selected_scripture}")
    except Exception as e:
        logging.error(f"Error writing random scripture to agenda file: {e}")

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(filepath):
    """Sends the file as an email."""
    logging.info("Step 2n: Sending email.")

    # Email configuration - REPLACE WITH ACTUAL CREDENTIALS AND DETAILS
    sender_email = "your_email@example.com"
    sender_password = "your_email_password" # Use environment variables or a secure method for production
    receiver_email = "recipient@example.com"
    smtp_server = "smtp.example.com"
    smtp_port = 587 # or 465 for SSL

    if not os.path.exists(filepath):
        logging.error(f"File not found for email attachment: {filepath}")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"Prayer Breakfast Agenda - {os.path.basename(filepath).replace('.html', '')}"

        # Attach the HTML file
        with open(filepath, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(filepath)}",
        )
        msg.attach(part)

        # Add a plain text body
        msg.attach(MIMEText("Please find attached the Prayer Breakfast Agenda.", "plain"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls() # Secure the connection
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        logging.info(f"Email sent successfully with attachment: {filepath}")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

def main():
    """Main function to execute all procedures."""
    setup_logging()
    logging.info("Starting prayer breakfast script.")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Step 2a
    agenda_file = duplicate_file(OUTPUT_DIR)
    if not agenda_file:
        return

    # Step 2b
    rename_title(agenda_file)

    # Step 2c
    bible_reading(agenda_file)

    # Step 2d
    prayer_card(agenda_file)

    # Step 2e
    international_reading(agenda_file)

    # Step 2f
    state_reading(agenda_file)

    # Step 2g
    widow_prayer(agenda_file)

    # Step 2h
    pastor_prayer(agenda_file)

    # Step 2i
    html_file = convert_file_to_html(agenda_file)

    # Step 2j
    if html_file:
        print_file(html_file)

    # Step 2k
    get_scripture(agenda_file)

    # Step 2l
    html_file_2 = convert_file_to_html(agenda_file)

    # Step 2m
    if html_file_2:
        print_file(html_file_2)

    # Step 2n
    send_email(agenda_file)

    logging.info("Script finished.")

if __name__ == "__main__":
    main()
