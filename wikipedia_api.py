import requests
from bs4 import BeautifulSoup
import csv
import psycopg2
from decimal import Decimal

# Connection parameters for the PostgreSQL database
connection_params = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'Countries',
    'user': 'postgres',
    'password': 'postgres',
    'sslmode': 'prefer',
    'connect_timeout': 10
}


def parse_countries():
    """
       Parse the CSV file containing country names.

       Returns:
           list: List of country names.
    """
    with open("countries.csv", mode="r", encoding="utf-8", newline="") as csvfile:
        csv_reader = csv.reader(csvfile)
        country_names = []
        for row in csv_reader:
            country_names.extend(row)
        return country_names

def check_page_exists(url):
    """
       Check if the given URL exists.

       Args:
           url (str): The URL to check.

       Returns:
           bool: True if the page exists, False otherwise.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return True
    return False


def extract_data(url):
    """
       Extract data from the given Wikipedia page URL.

       Args:
           url (str): The Wikipedia page URL.

       Returns:
           dict: Dictionary containing extracted data.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table", {"class": "infobox ib-country vcard"})

    if table is None:
        table = soup.find("table", {"class": "infobox ib-pol-div vcard"})
        if table is None:
            table = soup.find("table", {"class": "infobox"})
            if table is None:
                return {}

    data = {}

    for row in table.find_all("tr"):
        label = row.find("th", {"class": "infobox-label"})
        value = row.find("td", {"class": "infobox-data"})

        if label and value:
            label_text = label.text.strip()
            value_text = value.text.strip()

            # Process specific labels and extract corresponding data
            if label_text == "Official languages":
                languages = [lang.text.strip() for lang in value.find_all("a")]
                value_text = ", ".join(languages)

            # Add data to the dictionary if it's not already there
            if label_text not in data:
                data[label_text] = value_text

    new_data = {}
    for key in data.keys():
        if "Capital" in key or "Largest city" in key:
            capital_name = data[key]
            for i in range(len(capital_name)):
                if capital_name[i].isdigit():
                    capital_name = capital_name[:i]
                    break
            new_data["Capital"] = capital_name
        if "Time zone" in key:
            new_data["Time zone(s)"] = data[key]
        if "Government" in key:
            # remove the text between [] (including [])
            government = data[key]
            if government.find("[") != -1:
                start_index = government.find("[")
                end_index = government.find("]")
                government = government[:start_index] + government[end_index + 1:]
            new_data["Government"] = government
        if "languages" in key or "Languages" in key or "language" in key or "Language" in key:
            # add a command before each capital letter
            languages = data[key]
            new_languages = ""
            for i in range(len(languages)):
                if languages[i].isupper() and i != 0:
                    new_languages += ", "
                new_languages += languages[i]
            # remove the text between [] (including [])
            if new_languages.find("[") != -1:
                start_index = new_languages.find("[")
                end_index = new_languages.find("]")
                new_languages = new_languages[:start_index] + new_languages[end_index + 1:]
            new_data["Official languages"] = new_languages
        if "estimate" in key or "census" in key or ("Population" in key and "rank" not in key):
            # keep only the number till the first [
            population = data[key]
            for i in range(len(population)):
                if population[i] == "[" or population[i] == " " or population[i] == "(":
                    population = population[:i]
                    break
            # remove the , from the number
            new_data["Population"] = population
        if "Density" in key or "density" in key:
            # keep only the number/ km2, excluding /sq mi
            density = data[key]
            for i in range(len(density)):
                if density[i] == "/":
                    density = density[:i]
                    break
            new_data["Population density"] = density
        if "capita" in key:
            # keep only the number till the first [ or till the first space or till the first (
            gdp = data[key]
            for i in range(len(gdp)):
                if gdp[i] == "[" or gdp[i] == " " or gdp[i] == "(":
                    gdp = gdp[:i]
                    break
            # remove the $ from the number
            gdp = gdp.replace("$", "")
            new_data["GDP (PPP)"] = gdp
        if ("Total" in key or ("Area" in key and "rank" not in key)) and new_data.get("Area", "") == "" :
            # keep only the number till the first [ or till the first space
            area = data[key]
            for i in range(len(area)):
                if area[i] == "[" or area[i] == " ":
                    area = area[:i]
                    break
            # remove the km2 from the number
            area = area.replace("km2", "")
            area = area.replace(" ", "")

            # remove the sq mi from the number
            if area.find("sq") != -1:
                area = area.replace("sq", "")
                area = area.replace("mi", "")
                # convert the number to km2
                x = convert_to_numeric(area)
                x = float(x)
                x = x * 2.58999
                area = str(x)

            new_data["Area"] = area


    return new_data

def find_neighbours(country):
    data = {}
    url = "https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_number_of_land_borders"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table with the relevant information
    table = soup.find("table", {"class": "wikitable"})

    # Iterate through rows in the table
    for row in table.find_all("tr")[1:]:  # Skip the header row
        columns = row.find_all("td")

        if columns:  # Check if it's not an empty row
            neighbor_country = columns[0].find("a").text.strip()  # Extract neighbor country name
            neighbors = [n.strip() for n in columns[5].get_text("\n").split("\n") if n.strip()]  # Extract neighboring countries

            data[neighbor_country] = neighbors

    # Return the neighbors of the specified country
    if country in data:
        return data[country]
    else:
        return []

def insert_into_database(country, data_dict):
    """
       Insert data into the PostgreSQL database.

       Args:
           country (str): The name of the country.
           data_dict (dict): Dictionary containing data to be inserted.

       Returns:
           None
    """
    try:
        connection = psycopg2.connect(**connection_params)
        cursor = connection.cursor()

        # Create the table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                nume VARCHAR(255) PRIMARY KEY,
                nume_capitala VARCHAR(255),
                populatie NUMERIC(20, 0),
                densitate NUMERIC(20, 0),
                area NUMERIC(20, 0),
                gdp NUMERIC(20, 0),
                limba_vorbita VARCHAR(255),
                fus_orar VARCHAR(255),
                tip_regim VARCHAR(255),
                vecini VARCHAR(1000)
            );
        """)

        # Convertim variabilele numerice înainte de inserare
        populatie = convert_to_numeric(data_dict.get('Population', ''))
        densitate = convert_to_numeric(data_dict.get('Population density', ''))
        area =  convert_to_numeric(data_dict.get('Area', ''))
        gdp = convert_to_numeric(data_dict.get('GDP (PPP)', ''))
        # if we have both area and population, we can calculate the density
        if (populatie != 0 and area != 0) or densitate == 0:
            densitate = populatie / area

        # Insert data into the table
        cursor.execute("""
            INSERT INTO countries (
                nume, nume_capitala, populatie, densitate, area, gdp, limba_vorbita, fus_orar, tip_regim, vecini
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            country,
            data_dict.get('Capital', ''),
            populatie,
            densitate,
            area,

            gdp,
            data_dict.get('Official languages', ''),
            data_dict.get('Time zone(s)', ''),
            data_dict.get('Government', ''),
            ', '.join(data_dict.get('Neighbors', []))
        ))

        connection.commit()

    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def convert_to_numeric(value):
    """
    Convert a string value to a numeric value.

    Args:
        value (str): The input value to be converted.

    Returns:
        Decimal: The converted numeric value.
    """
    try:
        # Încercăm să convertim la float și apoi la Decimal pentru precizie
        if value is None:
            return 0
        numeric_value = Decimal(float(value.replace(',', '')))
        return numeric_value
    except (ValueError, TypeError):
        # În caz de eroare, putem returna None sau altă valoare implicită
        return 0

# Main function
def main():
    """
        Main function to process country data and insert it into the database.

        Returns:
            None
    """
    country_names = parse_countries()

    for country in country_names:
        url = f"https://en.wikipedia.org/wiki/{country.replace(' ', '_')}"
        if check_page_exists(url):
            data_extracted = extract_data(url)
            data_extracted['Neighbors'] = find_neighbours(country)
            insert_into_database(country, data_extracted)
            print(f"Data for {country} inserted into the database.")
        else:
            insert_into_database(country, {})
            print(f"No data found for {country}. Only country name inserted into the database.")

if __name__ == "__main__":
    main()
