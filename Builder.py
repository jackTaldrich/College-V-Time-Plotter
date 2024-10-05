import imaplib
import email
import unicodedata
from email.header import decode_header
import csv
import difflib
import re
import getpass
from datetime import datetime


class CollegeData:
    def __init__(self, data_file):
        self.college_dict = {}
        self.normalized_college_dict = {}
        with open(data_file, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                college_name = row['institution.displayName'].strip().lower()
                acceptance_rate = row['searchData.acceptanceRate.rawValue'].strip()
                self.college_dict[college_name] = acceptance_rate
                # Normalize the college name by removing 'university' and 'college'
                normalized_name = self.normalize_name(college_name)
                self.normalized_college_dict[normalized_name] = acceptance_rate

    @staticmethod
    def normalize_name(name):
        # Remove 'university' and 'college' from the name
        name = re.sub(r'\b(university|college)\b', '', name, flags=re.IGNORECASE)
        # Remove extra spaces and special characters, replace with dashes
        name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
        name = re.sub(r'\s+', '-', name.strip())  # Replace spaces with dashes
        return name.lower()

    def get_acceptance_rate(self, college_name):
        # Normalize the extracted college name
        normalized_college_name = self.normalize_name(college_name)
        # First, try exact match in normalized names
        if normalized_college_name in self.normalized_college_dict:
            return self.normalized_college_dict[normalized_college_name]
        # Try matching without normalization
        college_name_lower = college_name.lower()
        if college_name_lower in self.college_dict:
            return self.college_dict[college_name_lower]
        # Try substring match in normalized names
        for key in self.normalized_college_dict:
            if key in normalized_college_name or normalized_college_name in key:
                return self.normalized_college_dict[key]
        # Try fuzzy matching
        matches = difflib.get_close_matches(normalized_college_name,
                                            self.normalized_college_dict.keys(),
                                            n=1,
                                            cutoff=0.6)
        if matches:
            return self.normalized_college_dict[matches[0]]
        else:
            return None


class AcceptanceRateChecker:
    def __init__(self, college_data):
        self.college_data = college_data

    def get_acceptance_rate(self, college_name):
        acceptance_rate = self.college_data.get_acceptance_rate(college_name)
        if acceptance_rate:
            return acceptance_rate
        else:
            return None


class CollegeEmailChecker:
    def __init__(self, username, password, acceptance_rate_checker):
        self.username = username
        self.password = password
        self.acceptance_rate_checker = acceptance_rate_checker
        self.college_keywords = ['.edu', 'university', 'college', 'admissions']
        self.excluded_domains = ['vchsweb.org', 'collegeboard.org']
        self.excluded_senders = ['collegeboard']

    def check_emails(self):
        # Create an IMAP4 class with SSL
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        # Authenticate
        try:
            mail.login(self.username, self.password)
        except imaplib.IMAP4.error as e:
            print(f"Failed to login: {e}")
            return

        # Select the mailbox (INBOX)
        mail.select("inbox")

        # Format the date strings for the IMAP search
        current_date = datetime.now().strftime('%d-%b-%Y')

        since_date = input("\nChange start date or press enter to use default [01-May-2024]: ") or '01-May-2024'
        before_date = current_date

        status, messages = mail.search(None, f'(SINCE "{since_date}" BEFORE "{before_date}")')
        email_ids = messages[0].split()

        print(f"Total emails found: {len(email_ids)}")

        with open('college_emails.csv', mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date', 'College Name', 'Acceptance Rate']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for email_id in email_ids:
                # fetch email by id
                status, msg_data = mail.fetch(email_id, "(RFC822)")

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        from_ = msg.get("From")
                        date_ = msg.get("Date")

                        # parse to datetime object
                        email_date = self.parse_email_date(date_)
                        print(f"From: {from_}")
                        print(f"Date: {email_date}")

                        if from_:
                            from_lower = from_.lower()

                            # check if blacklisted
                            if any(excluded in from_lower for excluded
                                   in self.excluded_domains + self.excluded_senders):
                                print(f"This email is from an excluded sender or domain. Skipping.")
                                continue

                            if any(keyword in from_lower for keyword in self.college_keywords):
                                print(f"This email is from a college.")
                                # extract cleaner college name from the sender's display name
                                college_name = self.extract_college_name(from_)
                                if college_name:
                                    acceptance_rate = self.acceptance_rate_checker.get_acceptance_rate(college_name)
                                    if acceptance_rate:
                                        print(f"Acceptance rate for {college_name}: {acceptance_rate}%")
                                        # Write data to CSV file
                                        writer.writerow({
                                            'Date': email_date.strftime('%Y-%m-%d %H:%M:%S') if email_date else '',
                                            'College Name': college_name,
                                            'Acceptance Rate': acceptance_rate
                                        })
                                    else:
                                        print(f"Acceptance rate for {college_name} not found in data.")
                                else:
                                    print(f"Could not extract college name.")
                            else:
                                print(f"Not from a college.")
                        else:
                            print(f"No 'From' address found. Skipping email.")

        mail.logout()

    @staticmethod
    def parse_email_date(date_str):
        try:
            email_date = email.utils.parsedate_to_datetime(date_str)
            return email_date
        except Exception as e:
            print(f"Error parsing date: {e}")
            return None

    def extract_college_name(self, from_address):
        if "<" in from_address and "@" in from_address:
            display_name, email_address = from_address.split("<", 1)
            display_name = display_name.strip().replace('"', '')
            email_address = email_address.strip().strip(">")
        else:
            display_name = from_address.strip()
            email_address = None

        # if encoded decode
        try:
            decoded_display_name = email.header.decode_header(display_name)
            display_name_parts = []
            for part, encoding in decoded_display_name:
                if isinstance(part, bytes):
                    display_name_parts.append(part.decode(encoding or 'utf-8'))
                else:
                    display_name_parts.append(part)
            display_name = ''.join(display_name_parts)
        except Exception as e:
            print(f"Error decoding display name: {e}")

        display_name = display_name.strip().replace("'", "")

        display_name = unicodedata.normalize('NFKD', display_name)
        display_name = re.sub(r'\s+', ' ', display_name)

        if len(display_name.split()) <= 2 and not any(
                keyword.lower() in display_name.lower() for keyword in self.college_keywords):
            if email_address and "@" in email_address:
                domain = email_address.split("@")[1]
                domain_parts = domain.split('.')
                if len(domain_parts) > 2:
                    domain = '.'.join(domain_parts[-2:])
                college_name = self.domain_to_college_name(domain)
                if college_name:
                    return college_name
        else:
            college_name = self.format_college_name(display_name)
            return college_name

        return None  # extraction fails

    def domain_to_college_name(self, domain):
        domain = domain.lower().replace('www.', '').split('.')[0]

        domain_mappings = {
            'creighton': 'Creighton University',
            'ucdenver': 'University of Colorado Denver',
            'ttu': 'Texas Tech University',
            'bu': "Boston University",
        }

        if domain in domain_mappings:
            return self.format_college_name(domain_mappings[domain])

        return self.format_college_name(domain)

    @staticmethod
    def format_college_name(name):
        name = name.strip().replace("'", "")

        # don't ask me how this works
        patterns = [
            (r'\bU\b\.?\s*(of)?\s*(.*)', r'University of \2'),
            (r'\bUniv\b\.?\s*(of)?\s*(.*)', r'University of \2')
        ]

        for pattern, repl in patterns:
            new_name = re.sub(pattern, repl, name, flags=re.IGNORECASE)
            if new_name != name:
                name = new_name
                break

        # handling CU
        additional_patterns = [
            (r'\bCU\b', 'University of Colorado'),
            # Add more as needed
        ]

        for pattern, repl in additional_patterns:
            new_name = re.sub(pattern, repl, name, flags=re.IGNORECASE)
            if new_name != name:
                name = new_name
                break

        stopwords = ["admission", "admissions", "undergraduate", "office", "the", "at", "in", ".", ",", " "]
        words = [word for word in name.split() if word.lower() not in stopwords]

        # remove of if it's the last word
        if words and words[-1].lower() == 'of':
            words = words[:-1]

        cleaned_name = ' '.join(words)

        cleaned_name = cleaned_name.upper()
        cleaned_name = re.sub(r'[ ,]', '-', cleaned_name)
        cleaned_name = re.sub(r'-+', '-', cleaned_name)

        return cleaned_name


if __name__ == "__main__":
    print("This program uses the getpass library to securely allow you to type your password.")
    print("https://docs.python.org/3/library/getpass.html")
    print("Everything is open source; all data is LOCAL")
    input("Press Enter to continue.\n")

    username = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")

    # load college data
    college_data = CollegeData('data_reformatted.csv')
    acceptance_rate_checker = AcceptanceRateChecker(college_data)

    email_checker = CollegeEmailChecker(username, password, acceptance_rate_checker)
    email_checker.check_emails()
