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
driver.get("https://kurser.dtu.dk/search?CourseCode=+&SearchKeyword=++&SchedulePlacement=July&CourseType=&TeachingLanguage=")
driver.implicitly_wait(5)  # seconds

# Collect all course URLs
course_urls = []
course_elements = driver.find_elements(By.XPATH, "//a[starts-with(@href, '/course/')]")
for element in course_elements:
    if " - " in element.text:
        course_urls.append(element.get_attribute("href"))

# Extracting the course codes and details
courses = []
for url in course_urls:
    driver.get(url)
    wait = WebDriverWait(driver, 5)

    # Extract course details from the course page
    def get_course_detail(label_text):
        try:
            label_element = wait.until(EC.presence_of_element_located((By.XPATH, f"//td[label[contains(text(), '{label_text}')]]")))
            return label_element.find_element(By.XPATH, "following-sibling::td").text
        except Exception as e:
            return None
    def get_course_text_block(title):
        try:
            content_element = driver.find_element(By.XPATH, f"//div[div[contains(text(), '{title}')]]")
            return content_element.text.split(title)[1].strip()  # Split by title and take the second element
        except Exception as e:
            return None    

    course_code, course_name = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='pagecontents']/div[1]/div[1]/h2"))).text.split(" ", 1)
    english_title = get_course_detail('Engelsk titel')
    teaching_language = get_course_detail('Undervisningssprog')
    points = get_course_detail('Point( ECTS )')
    course_type = get_course_detail('Kursustype')
    schedule_placement = get_course_detail('Skemaplacering')
    teaching_place = get_course_detail('Undervisningens placering')
    teaching_form = get_course_detail('Undervisningsform')
    course_duration = get_course_detail('Kursets varighed')
    exam_schedule = get_course_detail('Eksamensplacering')
    evaluation_form = get_course_detail('Evalueringsform')
    exam_duration = get_course_detail('Eksamensvarighed')
    aids = get_course_detail('Hjælpemidler')
    grading_scale = get_course_detail('Bedømmelsesform')
    course_coordinator = get_course_detail('Kursusansvarlig')
    responsible_department = get_course_detail('Institut')
    course_goals = get_course_text_block('Overordnede kursusmål')
    learning_objectives = get_course_text_block('Læringsmål')
    course_content = get_course_text_block('Kursusindhold')

    info_link = wait.until(EC.presence_of_element_located((By.XPATH, "//a[text()='Information']"))).get_attribute('href')
    driver.get(url+"/info")
    

    course_data = {
        "code": course_code,
        "name": course_name,
        "url": url,
        "english_title": english_title,
        "teaching_language": teaching_language,
        "points": points,
        "course_type": course_type,
        "schedule_placement": schedule_placement,
        "teaching_place": teaching_place,
        "teaching_form": teaching_form,
        "course_duration": course_duration,
        "exam_schedule": exam_schedule,
        "evaluation_form": evaluation_form,
        "exam_duration": exam_duration,
        "aids": aids,
        "grading_scale": grading_scale,
        "course_coordinator": course_coordinator,
        "responsible_department": responsible_department,
          "course_goals": course_goals,
        "learning_objectives": learning_objectives,
        "course_content": course_content,
    }
    print(course_data)
    courses.append(course_data)

# Reference to the Firebase Realtime Database
ref = db.reference("/courses")
for course in courses:
    ref.push().set(course)

driver.quit()
