import time

import requests
from bs4 import BeautifulSoup
from nutils import Scraper
import csv
from selenium import webdriver
from typing import Dict, List

# https://www.freeformatter.com/html-formatter.html#before-output


BASE_URL = "https://smoothcomp.com"


def get_event_info(scraper, event_id: int):
    event_info = {}

    event_url = f"{BASE_URL}/en/event/{str(event_id)}"
    page_html = scraper.scrape_with_delay(event_url).text
    soup = BeautifulSoup(page_html, "html.parser")
    soup2 = soup.find("div", class_="event-title")
    event_info["event_id"] = event_id
    event_info["event_name"] = soup2.find("h1").text
    event_date = soup.find("div", class_="date").text.replace("\n", "")
    event_info["event_date"] = event_date
    return event_info


def write_event_info(event_info: dict):
    fieldnames = event_info.keys()
    with open("events.csv", "a", newline="", encoding="UTF-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write the header only if the file is empty
        if file.tell() == 0:
            writer.writeheader()

        # Write event_info as one row in the CSV
        writer.writerow(event_info)


def write_event_athletes(event_id: int, athletes: list):
    if not athletes:
        return

    fieldnames = athletes[0].keys()
    with open(f"athletes_{event_id}.csv", "a", newline="", encoding="UTF-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if file.tell() == 0:
            writer.writeheader()
        for athlete in athletes:
            writer.writerow(athlete)


def get_match_data_blobs(driver, matches_url: str):
    matches_list = []
    # matches_url = f"https://smoothcomp.com/en/event/{event_id}/schedule/matchlist?club=5203"
    driver.get(matches_url)

    time.sleep(3)
    page_html = driver.page_source

    soup = BeautifulSoup(page_html, "html.parser")
    # Filter out matches only
    matches = soup.find("div", class_="matches-list")

    category_data_divs_list = matches.find_all("div", class_="category-row")
    match_data_divs_list = matches.find_all("div", class_="match-row")

    # Creating a list with combined category and matchdata, as they are related
    all_matches_data_list = []

    # building data
    for counter in range(0, len(category_data_divs_list)):
        match_data = {}
        match_data["category-data"] = str(category_data_divs_list[counter])
        match_data["match-data"] = str(match_data_divs_list[counter])
        all_matches_data_list.append(match_data)

    return all_matches_data_list


def get_match_data(match_data: dict) -> dict:
    """
      Gets a datablob from a single get_match_data_blob and retrieves relevant data.
      Analyzes the match data and returns the analyzed result.

      Parameters:
      match_data_blob (dict): The single match data blob that needs data retrieval.

      Returns:
      dict: A dictionary containing the analyzed match data.
      """
    """ Data is built into a dict that is returned"""
    local_match_data = match_data["match-data"]
    soup = BeautifulSoup(str(local_match_data), "html.parser")

    fight_data = {}
    # Get mat and fightnumber
    fight_data["fight_number"] = soup.find("div", class_="number").text
    fight_data["fight_eta"] = soup.find("div", class_="eta").text

    # Get name and club for each participant
    participants = soup.find_all("span", class_="participant")

    # First Participant
    fight_data["first_participant_name"] = participants[0].contents[0].strip()
    fight_data["first_participant_club"] = participants[0].find("span", class_="club").text.strip()

    # Second Participant
    fight_data["second_participant_name"] = participants[1].contents[0].strip()
    fight_data["second_participant_club"] = participants[1].find("span", class_="club").text.strip()

    # Get profile URLs for each participant
    profiles = soup.find_all("a", class_="btn btn-sm btn-info profile")

    # First Participant
    fight_data["first_participant_profile"] = profiles[0]['href']

    # Second Participant
    fight_data["second_participant_profile"] = profiles[1]['href']

    # Getting the winner details
    winner_span = soup.find("span", class_="text-success")

    # Check if winner_span exists
    if winner_span is not None:
        winner = winner_span.parent.contents[0].strip()
        winner_statement = winner_span.text.strip()
        fight_data["winner_declared"]=True
        fight_data["winner_name"]=winner
        fight_data["win_description"] = winner_statement

        print(f'Winner Statement: {winner_statement}')
    else:
        fight_data["winner_declared"]=False

    return fight_data


def get_event_athletes(driver, event_id: int):
    participants_list = []
    participants_url = f"{BASE_URL}/en/event/{str(event_id)}/participants"
    driver.get(participants_url)
    time.sleep(3)
    # Scroll to bottom of the page
    # TODO: Make this smarter
    for _ in range(1, 30):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    page_html = driver.page_source
    soup = BeautifulSoup(page_html, "html.parser")
    profile_card = soup.findAll("div", class_="profile-card")

    for profile in profile_card:
        name = profile.find("div", class_="profile-card-name").span.text
        profile_link = profile.find("div", class_="profile-card-name").find("a")["href"]
        profile_id = profile_link[profile_link.rfind("/") + 1:]

        # Not all profile have countries mentioned
        try:
            country = profile.find("div", class_="country-name").span.text
        except AttributeError:
            country = "Unknown"

        birth_year = profile.find("div", class_="participant-td-birth").find("div").text
        event_age = profile.find("div", class_="participant-td-birth").find_all("div")[1].text
        participant_club_url = profile.find("div", class_="participant-td-club").find("a")["href"]
        participant_club_id = participant_club_url[participant_club_url.rfind("/") + 1:]
        participant_club_name = profile.find("div", class_="participant-td-club").find("a").text

        print(name)
        print(profile_link)
        print(profile_id)
        print(country)
        print(birth_year)
        print(event_age)
        print(participant_club_url)
        print(participant_club_id)
        print(participant_club_name)

        participant = {}
        participant["event_id"] = event_id
        participant["profile_id"] = profile_id
        participant["name"] = name
        participant["country"] = country
        participant["birth_year"] = birth_year
        participant["event_age"] = event_age
        participant["participant_club_url"] = participant_club_url
        participant["participant_club_id"] = participant_club_id
        participant["participant_club_name"] = participant_club_name

        participants_list.append(participant)
    return participants_list


def get_match_data_list(match_blobs):
    match_data_list = []
    for match in match_blobs:
        if match["match-data"] is not None:  # New check
            data = get_match_data(match)
            match_data_list.append(data)
        else:
            print("Knas")
    return match_data_list

def main():
    scraper = Scraper()
    driver = webdriver.Firefox()

    # print(f"Enter event ID:",end="")
    # event_id = input()
    event_id = "15675"

    # event_info = get_event_info(scraper, event_id)
    # write_event_info(event_info)

    # athletes = get_event_athletes(driver, event_id)
    # write_event_athletes(event_id, athletes)

    keiko_matches_data_blobs = get_match_data_blobs(driver,
                                              f"https://smoothcomp.com/en/event/{event_id}/schedule/matchlist?club=5203")

    keiko_match_data_list = get_match_data_list(keiko_matches_data_blobs)


    print("hepp")
    driver.quit()


main()
