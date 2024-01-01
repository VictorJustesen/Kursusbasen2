from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import firebase_admin
from firebase_admin import credentials, db
import time

# Initialize Firebase
cred = credentials.Certificate("./key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://kursusbasen-2-default-rtdb.europe-west1.firebasedatabase.app/'
})

# WebDriver setup
driver = webdriver.Chrome()
driver.get("https://kurser.dtu.dk/search?CourseCode=+&SearchKeyword=++&SchedulePlacement=July&CourseType=&TeachingLanguage=")  # URL shortened for readability
wait = WebDriverWait(driver, 10)
course_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[starts-with(@href, '/course/')]")))

# Extracting the course codes and details
courses = []
for element in course_elements:
    if " - " in element.text:
        course_code, course_name = element.text.split(" - ", 1)
        course_url = element.get_attribute("href")
        course_data = {
            "code": course_code,
            "name": course_name,
            "url": course_url
        }
        courses.append(course_data)

# Reference to the Firebase Realtime Database
ref = db.reference("/courses")
for course in courses:
    print(course)
    ref.push().set(course)

time.sleep(10)
driver.quit()
