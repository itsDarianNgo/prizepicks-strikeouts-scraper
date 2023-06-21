import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from fake_useragent import UserAgent
import csv
import time
import datetime
import random
import os
from git import Repo

# Set up a fake user agent
ua = UserAgent()
user_agent = ua.random


from git import Repo


# Function to push to GitHub
def push_to_git():
    repo = Repo("/home/azureuser/project/prizepicks-strikeouts-scraper")
    repo.git.add("--all")
    repo.git.commit("-m", "Update data")
    repo.git.push("origin", "main")


# Function for random sleep times
def random_sleep(min_time=5, max_time=15):
    sleep_time = random.uniform(min_time, max_time)
    time.sleep(sleep_time)


# Function to close the pop-up
def close_popup():
    # Wait for the pop-up to appear
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[3]/div/div/div[3]/button")))
    random_sleep()
    # Click the close button
    driver.find_element(By.XPATH, "/html/body/div[2]/div[3]/div/div/div[3]/button").click()


# Function to navigate to the PrizePicks MLB section
def navigate_to_mlb():
    driver.get("https://app.prizepicks.com/")
    close_popup()
    # Wait for the MLB tab to appear and click on it
    mlb_tab = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//div[text()="MLB"]')))
    random_sleep()
    mlb_tab.click()


# Function to navigate to the 'Pitcher Strikeouts' category
def navigate_to_pitcher_strikeouts():
    # Try to click on the 'Pitcher Strikeouts' category
    while True:
        try:
            # Wait until the category container is present on the page
            category_container = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".stat-container")))

            # Find all the category divs within the stat-container
            category_divs = category_container.find_elements(By.CSS_SELECTOR, ".stat")

            # Create a dictionary mapping category names to the corresponding WebElement
            categories = {div.text: div for div in category_divs}

            # Make sure 'Pitcher Strikeouts' is one of the categories
            if "Pitcher Strikeouts" not in categories:
                raise Exception("Could not find the 'Pitcher Strikeouts' category")

            random_sleep()
            categories["Pitcher Strikeouts"].click()

            # If the click was successful, break out of the loop
            break
        except StaleElementReferenceException:
            # If a StaleElementReferenceException was raised, try again
            continue


# Function to extract and save data
def scrape_and_save():
    start_time = time.time()  # Record the start time
    print("Scraping started at: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)))

    # Construct the filename using the current date
    directory = "data"
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, "mlb_pitcher_strikeouts_" + time.strftime("%Y_%m_%d") + ".csv")

    # Open the CSV file for appending
    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        # Write the header row if the file is empty
        if file.tell() == 0:
            writer.writerow(["Time of Scrape", "Player Name", "Team", "Position", "Game Start Date/Time", "Opponent", "Strikeout Predictions"])

        # Locate all the player elements
        player_elements = driver.find_elements(By.CLASS_NAME, "projection")

        # Loop over each player
        for player in player_elements:
            # Locate and extract each piece of data
            name = player.find_element(By.CLASS_NAME, "name").text
            team_position = player.find_element(By.CLASS_NAME, "team-position").text
            team, position = team_position.split(" - ")
            date = ", ".join([player.find_element(By.CLASS_NAME, "date").text.split(", ")[1] + ", " + str(datetime.datetime.now().year)])
            # split 'Tue, Jun 20 5:40 PM' into ['Tue', 'Jun 20 5:40 PM'], get the second element, add the current year and then join them together PM' into ['Tue', 'Jun 20 5:40 PM'], get the second element, and append the current year
            opponent = player.find_element(By.CLASS_NAME, "opponent").text.split(" ")[
                1
            ]  # split 'vs PHI' into ['vs', 'PHI'] and get the second element
            strikeout_predictions = player.find_element(By.XPATH, './/div[@class="presale-score"]').get_attribute("innerHTML")

            # Write the data to the CSV file
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), name, team, position, date, opponent, strikeout_predictions])

        end_time = time.time()  # Record the end time
        print("Scraping completed at: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)))
        print("Total scraping time: ", end_time - start_time, "seconds")

        driver.quit()


# Retry mechanism added to the main script
while True:  # Infinite loop
    options = uc.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--headless")  # Ensure GUI is off
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = uc.Chrome(options=options)
    try:
        navigate_to_mlb()
        navigate_to_pitcher_strikeouts()
        scrape_and_save()
        push_to_git()
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Retrying in 1 hour...")
        time.sleep(3600)
    finally:
        driver.quit()
    time.sleep(7200)
