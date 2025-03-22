import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Setup Selenium WebDriver (Headless Mode)
options = Options()
options.add_argument("--headless")  # Run without opening browser
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

# Initialize Chrome WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# CSV File Name (Overwrite Existing File)
csv_filename = "Courses2.csv"

# Column Headers
headers = ["Title", "Description", "URL", "Tag"]

# Write Headers to CSV (Overwrites File)
with open(csv_filename, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(headers)

# Function to Scrape Courses from Multiple Pages
def scrape_udacity_courses(pages=20):
    base_url = "https://www.udacity.com/catalog?page={}"  # Pagination URL format
    all_courses = []

    for page in range(1, pages + 1):
        print(f"Scraping Page {page}...")
        driver.get(base_url.format(page))
        #time.sleep(3)  # Wait for JavaScript to load content

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find all course elements
        courses = soup.find_all("a", class_="chakra-heading css-1msstcr")

        for course in courses:
            title = course.text.strip()
            url = "https://www.udacity.com" + course.get("href")
            description = "Not Available"
            tag = "Udacity"

            all_courses.append([title, description, url, tag])

    return all_courses

# Scrape 50 Pages
courses_data = scrape_udacity_courses(20)

# Write Data to CSV (Overwrite Mode)
with open(csv_filename, "a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(courses_data)

print(f"Scraping completed! Data saved to {csv_filename}")

# Close the Selenium Driver
driver.quit()
