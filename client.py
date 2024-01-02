import requests
import json
import argparse

def get_api_data(route):
    """
    Get data from a Flask API endpoint.

    Args:
        route (str): The route of the API endpoint.

    Raises:
        JSONDecodeError: If the response is not valid JSON.

    Returns:
        dict: Parsed JSON data received from the API.
    """
    api_url = 'http://localhost:5000'
    r = requests.get(api_url + route)

    if r.status_code == 200:
        try:
            data = r.json()
            return data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
    else:
        print(f"Error: {r.status_code}, {r.text}")

def main():
    """
    Main function to handle command line arguments and call the API.

    Parses the route argument provided via the command line,
    calls the `get_api_data` function, and prints the parsed JSON response.

    Raises:
        None

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description='Get data from a Flask API endpoint.')
    parser.add_argument('route', type=str, help='API endpoint route')

    args = parser.parse_args()
    route = args.route

    # Get data from the API
    api_data = get_api_data(route)

    if api_data:
        # Print the parsed JSON response
        print(f"Response:\n{json.dumps(api_data, indent=2)}")

if __name__ == '__main__':
    main()
