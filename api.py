from flask import Flask, jsonify
from flasgger import Swagger
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
Swagger(app)

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

def execute_query(query):
    """
    Execute a SQL query and fetch the results.

    Args:
        query (str): The SQL query to execute.

    Returns:
        list: A list of dictionaries representing the query results.
    """
    try:
        connection = psycopg2.connect(**connection_params)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/tara/<nume>', methods=['GET'])
def tara(nume):
    """
    Endpoint to get a specific country by name.

    ---
    parameters:
      - name: nume
        in: path
        type: string
        required: true
        description: The country name to search for.
    responses:
      200:
        description: The country with the specified name.
        examples:
            [{"nume": "Country1", "populatie": 100000000, "densitate": 100, "area": 1000000, "gdp": 1000000000, "limba_vorbita": "Language1", "fus_orar": "Timezone1"}]

    """
    query = f"SELECT nume, populatie, densitate, area, gdp, limba_vorbita, fus_orar, vecini FROM countries WHERE nume ILIKE '%{nume}%';"
    result = execute_query(query)
    return jsonify(result)

@app.route('/top-10-tari-populatie', methods=['GET'])
def top_10_populatie():
    """
    Endpoint to get the top 10 countries by population.

    ---
    responses:
      200:
        description: A list of countries with their population.
        examples:
          [{"nume": "Country1", "populatie": 100000000}, {"nume": "Country2", "populatie": 90000000}]
    """
    query = "SELECT nume, populatie FROM countries ORDER BY populatie DESC LIMIT 10;"
    result = execute_query(query)
    return jsonify(result)

@app.route('/top-10-tari-densitate', methods=['GET'])
def top_10_densitate():
    """
    Endpoint to get the top 10 countries by population density.

    ---
    responses:
      200:
        description: A list of countries with their population density.
        examples:
          [{"nume": "Country1", "densitate": 100}, {"nume": "Country2", "densitate": 90}]
    """
    query = "SELECT nume, densitate FROM countries ORDER BY densitate DESC LIMIT 10;"
    result = execute_query(query)
    return jsonify(result)

@app.route('/top-10-tari-suprafata', methods=['GET'])
def top_10_suprafata():
    """
    Endpoint to get the top 10 countries by land area.

    ---
    responses:
      200:
        description: A list of countries with their land area.
        examples:
          [{"nume": "Country1", "area": 1000000}, {"nume": "Country2", "area": 900000}]
    """
    query = "SELECT nume, area FROM countries ORDER BY area DESC LIMIT 10;"
    result = execute_query(query)
    return jsonify(result)

@app.route('/top-10-tari-gdp', methods=['GET'])
def top_10_gdp():
    """
    Endpoint to get the top 10 countries by GDP.

    ---
    responses:
      200:
        description: A list of countries with their GDP.
        examples:
          [{"nume": "Country1", "gdp": 1000000000}, {"nume": "Country2", "gdp": 900000000}]
    """
    query = "SELECT nume, gdp FROM countries ORDER BY gdp DESC LIMIT 10;"
    result = execute_query(query)
    return jsonify(result)

@app.route('/limba/<limba>', methods=['GET'])
def tari_cu_limba(limba):
    """
    Endpoint to get countries where the specified language is spoken.

    ---
    parameters:
      - name: limba
        in: path
        type: string
        required: true
        description: The language to search for.
    responses:
      200:
        description: A list of countries where the specified language is spoken.
        examples:
          [{"nume": "Country1"}, {"nume": "Country2"}]
    """
    query = f"SELECT nume FROM countries WHERE limba_vorbita ILIKE '%{limba}%';"
    result = execute_query(query)
    return jsonify(result)

@app.route('/fus-orar/<fus_orar>', methods=['GET'])
def tari_cu_fus_orar(fus_orar):
    """
    Endpoint to get countries in the specified time zone.

    ---
    parameters:
      - name: fus_orar
        in: path
        type: string
        required: true
        description: The time zone to search for.
    responses:
      200:
        description: A list of countries in the specified time zone.
        examples:
          [{"nume": "Country1"}, {"nume": "Country2"}]
    """
    query = f"SELECT nume FROM countries WHERE fus_orar ILIKE '%{fus_orar}%';"
    result = execute_query(query)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
