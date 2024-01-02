import requests
from bs4 import BeautifulSoup
import csv

def get_wikipedia_page_content(url):
    """
    Send a GET request to the provided URL and return the parsed HTML content.

    Args:
        url (str): The URL of the Wikipedia page.

    Returns:
        BeautifulSoup: Parsed HTML content.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.content, "html.parser")
    else:
        print("Error accessing the website. Status code:", response.status_code)
        return None

def extract_country_names(table):
    """
    Extract country names from the provided HTML table.

    Args:
        table (BeautifulSoup): The HTML table containing country data.

    Returns:
        list: List of cleaned country names.
    """
    country_names = []
    rows = table.find_all("tr")[1:]

    for row in rows:
        if row.find("th"):
            continue

        cells = row.find_all("td")
        country_name = cells[0].text.strip()

        # Clean up country names
        country_name = clean_country_name(country_name)

        if country_name.find("\xa0") != -1:
            country_name = cells[1].text.strip()

        country_names.append(country_name)

    return country_names

def clean_country_name(country_name):
    """
    Clean up the provided country name by removing unwanted text.

    Args:
        country_name (str): The original country name.

    Returns:
        str: Cleaned country name.
    """
    # Remove text between parentheses
    country_name = remove_text_between_symbols(country_name, "(", ")")
    # Remove text between square brackets
    country_name = remove_text_between_symbols(country_name, "[", "]")
    # Remove text after '-'
    country_name = remove_text_after_symbol(country_name, "– See")
    # Remove whitespace character  
    country_name = country_name.replace("\u200a", "")

    return country_name

def remove_text_between_symbols(text, start_symbol, end_symbol):
    """
    Remove text between specified symbols from the provided text.

    Args:
        text (str): The original text.
        start_symbol (str): The starting symbol.
        end_symbol (str): The ending symbol.

    Returns:
        str: Text after removing content between symbols.
    """
    start_index = text.find(start_symbol)
    end_index = text.find(end_symbol)
    if start_index != -1 and end_index != -1:
        return text[:start_index] + text[end_index + 1:]
    return text

def remove_text_after_symbol(text, symbol):
    """
    Remove text after the specified symbol from the provided text.

    Args:
        text (str): The original text.
        symbol (str): The symbol to find.

    Returns:
        str: Text after removing content after the symbol.
    """
    start_index = text.find(symbol)
    if start_index != -1:
        return text[:start_index]
    return text

def write_to_csv(file_path, data):
    """
    Write the provided data to a CSV file.

    Args:
        file_path (str): The path to the CSV file.
        data (list): List of data to write to the file.

    Returns:
        None
    """
    with open(file_path, mode="w", encoding="utf-8", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(data)

def main():
    """
        Main function to scrape country names from the Wikipedia page and generate a CSV file.

        The function performs the following steps:
        1. Retrieves HTML content from the Wikipedia page.
        2. Finds the table containing the ISO 3166 country codes.
        3. Extracts and cleans country names from the table.
        4. Writes the cleaned country names to a CSV file.

        Returns:
            None
    """
    # URL of the Wikipedia page
    url = "https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes"

    # Get HTML content from the Wikipedia page
    soup = get_wikipedia_page_content(url)

    if soup:
        # Find the table containing the country data
        table = soup.find("table", {"class": "wikitable"})

        # Extract and clean country names
        country_names = extract_country_names(table)

        # Write country names to CSV file
        write_to_csv("countries.csv", country_names)

        print("CSV file generated successfully.")

if __name__ == "__main__":
    main()
