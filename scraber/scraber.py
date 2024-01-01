from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate("./key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://kursusbasen-2-default-rtdb.europe-west1.firebasedatabase.app/'
})

# WebDriver setup
driver = webdriver.Chrome()
driver.get("https://kurser.dtu.dk/search?CourseCode=0103&SearchKeyword=++&CourseType=&TeachingLanguage=")
driver.implicitly_wait(3)  # Reduced wait time to 3 seconds

# Collect all course URLs
course_urls = []
course_elements = driver.find_elements(By.XPATH, "//a[starts-with(@href, '/course/')]")
for element in course_elements:
    if " - " in element.text:
        course_urls.append(element.get_attribute("href"))

# Helper function to extract the number of attendees, passed, and average grade
def get_grade_data(course_code, season, year):

    driver.get(f"https://karakterer.dtu.dk/Histogram/1/{course_code}/{season}-{year}")
    wait = WebDriverWait(driver, 3)  # Reduced wait time to 3 seconds

    # Extract the number of attendees
    try:
        attendees_element = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Antal tilmeldte')]/../td[2]")))
        attendees = int(attendees_element.text)
    except Exception as e:
        attendees = None
        #print(f"Error extracting attendees: {e}")
    
    # Extract the number of passed students and average grade
    passed = None
    average_grade = None
    try:
        passed_element = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Antal bestået')]/../td[2]")))
        passed = int(passed_element.text.split()[0])
    except Exception as e:
        pass
        #print(f"Error extracting passed students: {e}")


# Try to extract the average grade
    try:
        average_grade_element = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Eksamensgennemsnit')]/../td[2]")))
        average_grade_text = average_grade_element.text.strip()[0]
        average_grade = float(average_grade_text) if average_grade_text != "Intet eksamensgennemsnit" else None
    except Exception as e:
        pass
        #print(f"Error extracting average grade: {e}")

    return attendees, passed, average_grade

# Extracting the course codes and details
courses = []
for url in course_urls:
    driver.get(url)
    wait = WebDriverWait(driver, 5)  # Reduced wait time to 3 seconds

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

   # first page
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

       # haunted second page grades 
    current_year = datetime.now().year
    current_month = datetime.now().month

    if 5 < current_month >= 11:
        current_season = 'Summer'
        previous_season = 'Winter'
        previous_year = current_year - 1
        two_seasons_ago_season = 'Summer'
        two_seasons_ago_year = current_year - 1
    else:
        current_season = 'Winter'
        previous_season = 'Summer'
        current_year = current_year-1
        previous_year = current_year
        two_seasons_ago_season = 'Winter'
        two_seasons_ago_year = current_year - 1

    # Get grade data for the current, previous, and two seasons ago
    current_attendees, current_passed, current_grades = get_grade_data(course_code, current_season, current_year)
    previous_attendees,previous_passed, previous_grades = get_grade_data(course_code, previous_season, previous_year)
    two_seasons_ago_attendees,two_seasons_ago_passed, two_seasons_ago_grades = get_grade_data(course_code, two_seasons_ago_season, two_seasons_ago_year)
    print(current_attendees, current_passed, current_grades, previous_attendees, previous_passed, previous_grades, two_seasons_ago_attendees, two_seasons_ago_passed, two_seasons_ago_grades)
    
    grades = current_grades
    attendees = current_attendees
    passed = current_passed
    if attendees is None or previous_attendees//attendees*2:
        grades = previous_grades
        attendees = previous_attendees
        passed = previous_passed
    if attendees is None or two_seasons_ago_attendees>attendees*2:
        grades = two_seasons_ago_grades
        attendees = two_seasons_ago_attendees
        passed = two_seasons_ago_passed
   
   #eval
        try:
            driver.get(f"kurser.dtu.dk/course/{course_code}/info")
            wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div/div[1]/div/div[2]/a"))).click()
        except Exception as e:
            
            pass

    

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
        "grade_avg" : grades,
        "attendees" : attendees,
        "passed" : passed,
    }
    print(grades, attendees, passed)
    #courses.append(course_data)

# Reference to the Firebase Realtime Database
ref = db.reference("/courses")
for course in courses:
    ref.push().set(course)

driver.quit()
