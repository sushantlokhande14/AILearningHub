import requests
from bs4 import BeautifulSoup
import csv
import time

# Base URL format for pagination
base_url = "https://www.coursera.org/search?query=AI&page={}"

# Headers to mimic a real browser
headers = {"User-Agent": "Mozilla/5.0"}

# File name (to be reused for other sites later)
csv_filename = "Courses1.csv"

# Column headers
columns = ["Title", "Description", "URL", "Tag"]

# List to store course data
courses_data = []

# Iterate through the first 5 pages
for page in range(1, 21):
    print(f"Scraping page {page}...")
    url = base_url.format(page)
    
    # Send request
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page {page}, skipping...")
        continue  # Skip this page if request fails

    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all course cards
    courses = soup.find_all("div", class_="cds-ProductCard-content")  # Adjust this selector if needed

    for course in courses:
        # Extract course title
        title_tag = course.find("h3", class_="cds-CommonCard-title")
        title = title_tag.text.strip() if title_tag else "No title found"

        # Extract course URL
        link_tag = course.find("a")
        course_url = f"https://www.coursera.org{link_tag['href']}" if link_tag else "No URL"

        # Extract course description (if available)
        description = link_tag["aria-label"] if link_tag and "aria-label" in link_tag.attrs else "No description available"

        # Store data with "Coursera" tag
        courses_data.append([title, description, course_url, "Coursera"])

    # Pause to avoid being blocked
    #time.sleep(2)

# Overwrite `courses.csv` to ensure clean data every time
with open(csv_filename, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    #writer.writerow(columns)  # Write column headers
    writer.writerows(courses_data)  # Write scraped data

print(f"Scraping complete! Data saved in {csv_filename}")

# Print first 10 courses
for course in courses_data[:10]:
    print(course)
