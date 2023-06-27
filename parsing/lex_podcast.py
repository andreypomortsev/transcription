#!/usr/bin/env python3
""" Module parses the lexfridman.com/podcast and return information about all podcasts
in format of a csv file delimited by a ','.

The csv file consists the next fields:
    - title (str): the title of the episode.
    - guest (str): the name of the guest featured in the episode.
    - description (str): a brief description of the contents of the episode.
    - duration (str): the length of the episode, in the format "HH:MM:SS".
    - youtube_url (str): the URL of the YouTube video, if available.
    - audio_file_url (str): the URL of the audio file associated with the episode.
    - thumbnail_url (str): the URL of the thumbnail image for the episode.
    - date (datetime.date): date the podcast was uploaded on youtube.com.
    - time (datetime.time): time the podcast was uploaded on youtube.com.
"""
import csv
import re
from datetime import datetime
import io
import logging
import os
import time as time_to_sleep
from dotenv import load_dotenv
import requests
import random
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3
import googleapiclient.discovery
from googleapiclient.errors import HttpError

load_dotenv()
api_key = os.getenv("api_key")

logging.basicConfig(
    format="%(asctime)s %(message)s", filename="errors.log", level=logging.ERROR
)


def get_description(url: str) -> str:
    """Retrieves the description text of a Lex Fridman podcast episode
    from a given URL.

    Args:
        url: A string representing the URL of the podcast episode page.

    Returns:
        A string representing the description text of the podcast episode,
        or an empty string if no description text is found.

    Raises:
        requests.exceptions.RequestException: if there is an error
        retrieving the web page from the specified URL.
    """
    response = requests.get(url, timeout=5)
    soup = BeautifulSoup(response.content, "html.parser")

    text_div = soup.find("div", {"class": "entry-content"})
    try:
        text = text_div.find_all("p")
        if len(text) > 2:
            if "Please" in text[2].text:
                indx = text[2].text.index(" Please ")
                result = text[2].text[:indx]
                return result
            result = text[2].text
            return result
        result = text_div.find("span").text
        return result
    except Exception as error:
        logging.exception("Couldn't find any description in podcast %s, %s", url, error)
        return None


def get_duration(mp3_url: str) -> float:
    """
    Return the duration of an MP3 audio file located at the specified URL.

    Args:
        mp3_url (str): A string representing the URL of the MP3 audio file.

    Returns:
        A float representing the length of the MP3 audio file in seconds,
        rounded to 2 decimal places.

    Raises:
        IOError: If there is an I/O error while retrieving the MP3 audio file from 'mp3_url'.
        MutagenError: If there is an error while extracting metadata from the MP3 audio file.

    Example:
        >>> get_duration('https://example.com/audio.mp3')
        127.89
    """
    try:
        # Retrieve the MP3 audio file using the provided URL
        response = requests.get(mp3_url, timeout=5)

        # Read the MP3 audio file into a bytes buffer using io.BytesIO
        with io.BytesIO(response.content) as mp3_buffer:
            # Use mutagen to extract metadata from the MP3 audio file
            mp3 = MP3(mp3_buffer)

            # Return the length of the MP3 audio file in seconds, rounded to 2 decimal places
            return round(mp3.info.length, 2)
    except requests.exceptions.RequestException as error:
        # Raise an exception if there is an error retrieving the MP3 audio file
        logging.debug("Error retrieving MP3 file from %s: %s", mp3_url, error)
        return 0


def get_date_time(youtube_video_id: str, api_key: str) -> tuple:
    """
    Retrieves the date and time when a YouTube video was uploaded, given its
    video ID and a valid YouTube Data API key.

    Args:
        youtube_video_id (str): The 11-character video ID of the desired YouTube video.
        api_key
     (str): A valid YouTube Data API key with the 'youtube.readonly' scope.

    Returns:
        A tuple containing the date and time when the video was uploaded on YouTube,
        in the format 'YYYY-MM-DD HH:MM:SS'. If the video ID is invalid or the API call
        fails, the function returns None.
    """
    # Create a YouTube Data API client using the provided API key
    if not youtube_video_id:
        logging.exception("Youtube id can't be %s, fix the input", youtube_video_id)
        return None

    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    # Retrieve the video snippet using the video ID
    request = youtube.videos().list(part="snippet", id=youtube_video_id)
    response = request.execute()

    # Extract the upload date and time from the video snippet
    try:
        upload_date = response["items"][0]["snippet"]["publishedAt"]
        upload_date = upload_date.replace("Z", "+00:00")  # Convert to UTC time zone
        upload_datetime = datetime.fromisoformat(upload_date)
        upload_datetime_str = upload_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_time = convert_to_timestamp(upload_datetime_str)
        return date_time
    except (KeyError, IndexError) as error:
        # If the video ID is invalid or the API call fails, return None
        logging.exception(
            "Error retrieving upload time file with id %s to youtube: %s",
            youtube_video_id,
            error,
        )
        return None
    except HttpError as error:
        logging.exception(
            "There is some problem with either the api key or with the Internet %s",
            error,
        )
        return None


def convert_to_timestamp(date_str: str) -> tuple:
    """
    Convert a string representing a date and time in ISO 8601 format
    to separate date and time objects.

    Args:
        date_str (str): A string representing a date and time in ISO 8601 format
        e.g. '2022-11-04T16:09:32Z'.

    Returns:
        A tuple containing two objects: a 'date' object representing
        the date portion of the input string,
        and a 'time' object representing the time portion of the input string.

    Example:
        >>> convert_to_timestamp('2022-11-04T16:09:32Z')
        (datetime.date(2022, 11, 4), datetime.time(16, 9, 32))
    """
    try:
        # Parse the input string as a datetime object
        timestamp = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as error:
        # Raise an error if the input string is not in the expected format
        logging.exception("Invalid ISO 8601 format: %s: %s", date_str, error)
        return 0, 0

    # Extract the date and time components from the datetime object
    date = timestamp.date()
    time = timestamp.time()

    # Return the date and time components as a tuple
    return date, time


def get_youtube_id(youtube_url: str) -> str:
    """
    Extracts the YouTube video ID from a YouTube URL in the format
    'https://www.youtube.com/watch?v=XXXXXXXXXXX' and returns it as a string.

    Args:
        youtube_url (str): A string containing a valid YouTube video URL.

    Returns:
        A string containing the 11-character YouTube video ID, or None if the URL
        is not in the correct format.
    """
    # Search for the video ID in the URL using a regular expression
    match = re.search(r"youtube\.com\/watch\?v=(\w+)", youtube_url)

    # If a match is found, extract the video ID from the match object
    if match:
        video_id = match.group(1)
        return video_id

    # If no match is found add the info to the logging, and return None
    logging.exception(
        "Can't extract the video ID from the match object from the url %s", youtube_url
    )
    return None


def check_url_response(url: str) -> str:
    """Send an HTTP GET request to the given URL and return the URL
    if the response status code is 200 OK.

    Args:
        url: A string representing the URL to request.

    Returns:
        If the response status code is 200 OK, return the input URL.
        Otherwise, return None.
    """
    response = requests.get(url, timeout=5)
    if response.status_code == requests.codes.ok:
        return url
    logging.exception("The url %s responce code is %s", url, response.status_code)
    return None


def get_audio_file_url(podcast_url: str) -> str:
    """
    Given a podcast URL, retrieves the URL of the audio file associated with podcast episode.

    Args:
        podcast_url: A string containing the URL of the podcast episode page.

    Returns:
        A string containing the URL of the audio file, or None if the URL cannot be retrieved.
    """
    try:
        response = requests.get(podcast_url, timeout=5)
    except requests.exceptions.RequestException as error:
        logging.exception(
            "The url %s responce code is %s. Error: %s.",
            podcast_url,
            response.status_code,
            error,
        )
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    try:
        audio_file_url = soup.find("a", {"class": "powerpress_link_pinw"})["href"]
        return check_url_response(audio_file_url)
    except TypeError as error:
        logging.exception("The url %s is incorrect. Error: %s.", podcast_url, error)
        return None


def get_audio_name(thumbnail_url: str, podcast_url: str) -> str:
    """
    Given a thumbnail URL and a podcast URL, retrieves the URL of the audio file
    for the podcast episode.

    Args:
        thumbnail_url: A string containing the URL of the podcast episode thumbnail image.
        podcast_url: A string containing the URL of the podcast episode page.

    Returns:
        A string containing the URL of the audio file, or None if the URL cannot be retrieved.
    """
    pattern = r"^https:\/\/lexfridman\.com\/files\/thumbs_ai_podcast\/(.*)\.png$"
    match = re.search(pattern, thumbnail_url)
    if match:
        file_name = match.group(1)
        audio_file_url = (
            f"https://content.blubrry.com/takeituneasy/lex_ai_{file_name}.mp3"
        )
        if check_url_response(audio_file_url):
            return audio_file_url
        audio_file_url = (
            f"https://content.blubrry.com/takeituneasy/mit_ai_{file_name}.mp3"
        )
        if check_url_response(audio_file_url):
            return audio_file_url

    audio_file_url = get_audio_file_url(podcast_url)
    return audio_file_url


def get_data() -> set:
    """
    Retrieves podcast episode data from "https://lexfridman.com/podcast/" and
    collects the title, guest name, description, duration, YouTube URL,
    audio file URL, and thumbnail URL for each episode.

    Returns:
        A set of tuples, where each tuple contains the metadata for
        a single podcast episode.
        The tuples are structured as follows:
            - title (str): the title of the episode.
            - guest (str): the name of the guest featured in the episode.
            - description (str): a brief description of the contents of the episode.
            - duration (str): the length of the episode, in the format "HH:MM:SS".
            - youtube_url (str): the URL of the YouTube video, if available.
            - audio_file_url (str): the URL of the audio file associated with the episode.
            - thumbnail_url (str): the URL of the thumbnail image for the episode.
            - date (datetime.date): date the podcast was uploaded on youtube.com.
            - time (datetime.time): time the podcast was uploaded on youtube.com.
    """
    url = "https://lexfridman.com/podcast/"
    csv_episodes = set()
    try:
        response = requests.get(url, timeout=5)
    except requests.exceptions.RequestException as error:
        logging.exception(
            "The url %s responce code is %s. Error: %s.",
            url,
            response.status_code,
            error,
        )
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    episods = soup.find_all("div", {"class": "guest"})
    for episode in episods[:5]:
        time_to_sleep.sleep(round(random.uniform(0.00, 3.00), 2))
        try:
            youtube_url, podcast_page = [
                link["href"] for link in episode.select("div.vid-materials a")[:2]
            ]
            title = episode.select_one(".vid-title a").text
            guest = episode.select_one(".vid-person").text
            thumbnail_url = episode.select_one(".thumb-youtube img")["src"]
            description = get_description(podcast_page)
            audio_file_url = get_audio_name(thumbnail_url, podcast_page)
            duration = get_duration(audio_file_url)
            youtube_video_id = get_youtube_id(youtube_url)
            date, time = get_date_time(youtube_video_id, api_key)
            record = (
                title,
                guest,
                description,
                duration,
                youtube_url,
                audio_file_url,
                thumbnail_url,
                date,
                time,
            )
            duplicate_score = 0
            if record in csv_episodes:
                duplicate_score += 0.5
                if duplicate_score == 1:
                    return csv_episodes
            csv_episodes.add(record)
        except Exception as error:
            logging.exception("There is %s in %s", error, title)
            continue
    return csv_episodes


def save_list_to_csv(data: list, file_name: str) -> None:
    """Write the data to a CSV file with the given file_name.

    Args:
        data: A list of tuples, where the first tuple is a header and
        each next tuple represents a row in the CSV file.
        file_name: A string representing the file_name for the output CSV file.
    """
    with open(f"{file_name}.csv", "w", newline="", encoding="UTF-8") as file:
        writer = csv.writer(file)

        # Write header row
        header = (
            "title",
            "guest",
            "description",
            "duration",
            "youtube_url",
            "audio_file_url",
            "thumbnail_url",
            "date",
            "time",
        )
        writer.writerow(header)

        # Write data rows
        for row in data:
            writer.writerow(row)


if __name__ == "__main__":
    data_list = get_data()
    save_list_to_csv(data_list, "lex_podcasts")
