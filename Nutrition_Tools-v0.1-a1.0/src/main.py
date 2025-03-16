import csv
import os
import yaml
import requests
import set_api_key
from ratelimit import limits, sleep_and_retry
from fuzzywuzzy import process
import pint
import logging

#  Define rate limit:
RATE_LIMIT = 1000
PERIOD = 3600

#  Configure logging
LOG_FILE = "recipe_nutrition.log"
LOG_LEVEL = logging.INFO  #  Set desired logging level here
LOG_FORMAT = '%(asctime)s - %(lineno)d - %(levelname)s - %(message)s'  #  Time - Line number - Level - Message

PRINT_LEVEL = logging.WARNING  #  Set desired logging level to print to console here
PRINT_FORMAT = '%(levelname)s - %(message)s'  #  Level - Message
'''
Logging levels:
DEBUG: Includes YAML dumps of the nutrition data
INFO: Logs at the beginning and end of each function, within loops, and at decision points.
WARNING: Logs when an error that will not impact output accuracy occurs (e.g. substituting external source portionData if the FDC data is missing)
ERROR: Logs when an error that will impact output accuracy occurs (e.g. missing nutrient data)
CRITICAL: Logs when an error that will cause the program to stop occurs (e.g. missing API key)
'''
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(LOG_LEVEL)
formatter = logging.Formatter(LOG_FORMAT)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(PRINT_LEVEL)
stream_formatter = logging.Formatter(PRINT_FORMAT)
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)

logger.info("Logging initialized.")

#  Initialize the unit registry
ureg = pint.UnitRegistry()

def get_fdc_api_key():
    #  Readability function, returns the FDC API key from os.environ
    return os.environ.get('API_FoodData_Central')

def load_ingredients_from_csv():
    """
    Loads a list of ingredients and their quantities from a CSV file.
    Rows should be formatted as 'ingredient, quantity, unit'.
    
    Inputs:
    None (this function prompts user for the CSV file name)
    
    Outputs:
    dict: A dictionary with ingredient names as keys and a nested dictionary as a value for each ingredient.
    Example: ingredients: {'Flour': {'quantity': '1', 'unit': 'cup'}}
    """
    logger.info("Loading ingredients from CSV.")
    file_name = input("Please enter the name of the CSV file: ")
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    logger.info(f"File path: {file_path}")
    ingredients = {}

    try:
        with open(file_path, mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if len(row) != 3:
                    logger.warning(f"Skipping invalid row: {row}")
                    continue
                ingredient, quantity, unit = row
                ingredients[ingredient.strip()] = {
                    "quantity": quantity.strip(),
                    "unit": unit.strip()
                }
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except Exception as e:
        logger.critical(f"An error occurred: {e}")
        logger.exception(e)
    logger.info(f"Ingredients loaded:")
    logger.info(yaml.dump(ingredients, indent=2))
    return ingredients

@sleep_and_retry
@limits(calls=RATE_LIMIT, period=PERIOD)
def search_food(ingredient, api_key):
    """
    Searches the FoodData Central API for the given ingredient.
    
    Inputs:
    ingredient (str): The name of the ingredient to search for.
    api_key (str): The API key for accessing the FoodData Central API.
    
    Outputs:
    list: A list of search results (foods) if successful, otherwise None.
    """
    logger.info("Beginning Search.")
    base_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        'api_key': api_key,
        'query': ingredient,
        'dataType': "Foundation",
        'pageSize': 5,
    }
    if not api_key:
        logger.critical("API key not found.")
        return None
    
    logger.info(f"Searching for {ingredient}...")
    logger.info("Begin API request.")
    try:        
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        logger.info("API request successful.")
        return response.json().get('foods', [])
    except requests.exceptions.RequestException as e:
        logger.critical(f"Error making API request: {e}")
        logger.exception(e)
        return None

def best_match(ingredient, api_key):
    """
    Uses fuzzy matching to find the best match for the given ingredient in the FoodData Central API results.
    
    Inputs:
    ingredient (str): The name of the ingredient to search for.
    api_key (str): The API key for accessing the FoodData Central API.
    
    Outputs:
    int: The FDC ID of the best matching food if found, otherwise None.
    """
    logger.info(f"Finding best match for '{ingredient}'")
    if not api_key:
        logger.critical("API key not found.")
        return None
    results = search_food(ingredient, api_key)
    logger.debug(yaml.dump(results, indent=2))
    if not results:
        logger.error(f"No results found for '{ingredient}'")
        return None
    
    # Extract the descriptions
    descriptions = [result['description'] for result in results]

    # Find the best match using fuzzy matching
    best_match_description, _ = process.extractOne(ingredient, descriptions)

    # Find the FDC ID of the best match
    for result in results:
        if result['description'] == best_match_description:
            logger.info(f"Best match found: {best_match_description}")
            simaliarity = process.extract(ingredient, best_match_description)
            logger.debug(f"Similarity: {simaliarity}")
            return result['fdcId']
    #TODO Return the best match FDC ID, and the name of the best match as a tuple to allow for user confirmation.
    return None

@sleep_and_retry
@limits(calls=RATE_LIMIT, period=PERIOD)
def search_food_by_id(fdc_id, api_key):
    """
    Searches the FoodData Central API for the given food by its FDC ID.
    
    Inputs:
    fdc_id (int): The FDC ID of the food to search for.
    api_key (str): The API key for accessing the FoodData Central API.
    
    Outputs:
    dict: The full food data if successful, otherwise None.
    """
    logger.info(f"Searching for food with FDC ID: {fdc_id}")
    base_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
    params = {
        'api_key': api_key,
        'dataType': "Foundation",
        'pageSize': 5,
    }

    logger.info(f"Begin API request for FDC ID: {fdc_id}")
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        logger.info("API request successful.")
        logger.debug(yaml.dump(response.json(), indent=2))
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.critical(f"Error making API request: {e}")
        logger.exception(e)
        return None

def export_to_YAML(food_data, filename):
    """
    Exports the given food data to a YAML file.
    
    Inputs:
    food_data (dict): The food data to export.
    filename (str): The name of the YAML file to create.
    
    Outputs:
    None (Exports a YAML file)
    """
    try:
        with open(filename, 'w', encoding='utf-8') as yaml_file:
            yaml.dump(food_data, yaml_file, allow_unicode=True)
        logger.info(f"Food data exported to {filename}")
    except IOError as e:
        logger.error(f"Error exporting to YAML: {e}")
        logger.exception(e)

def process_food(food_data):
    """
    Processes the food data to extract nutrition information.
    
    Inputs:
    food_data (dict): The full food data dict from the FoodData Central API.
    
    Outputs:
    dict: A dictionary with processed food data. Strips out unnecessary information and extracts nutrients and portions.
    If no data is found, returns None.
    """   
    if not food_data:
        logger.critical("Error: No food data received.")
        return None
    
    logger.info(f"Processing food data for {food_data.get('description')}")
    processed_food = {
        "fdcId": food_data.get('fdcId'),
        "description": food_data.get('description'),
        "foodCategory": food_data.get('foodCategory', {}).get('description'),
        "nutrients": [],
        "portions": [],
    }

    # Extract nutrients
    if "foodNutrients" in food_data:
        logger.info(f"Nutrition data found for {food_data.get('description')}")
        for nutrient in food_data['foodNutrients']:
            logger.debug(f"Begin processing nutrient: {nutrient.get('nutrient', {}).get('name')}")
            nutrient_data = {
                "name": nutrient.get('nutrient', {}).get('name'),
                "unitName": nutrient.get('nutrient', {}).get('unitName'),
                "value": nutrient.get('amount'),
            }
            if nutrient_data['value'] is not None:                
                processed_food['nutrients'].append({
                    "name": nutrient.get('nutrient', {}).get('name'),
                    "unitName": nutrient.get('nutrient', {}).get('unitName'),
                    "value": nutrient.get('amount'),
                })
            else:
                logger.warning(f"Skipping nutrient: {nutrient_data}, value is None.")
            logger.debug(f"End processing nutrient: {nutrient.get('nutrient', {}).get('name')}")
    else:
        logger.critical(f"No nutrition data found for {food_data.get('description')}")
        return None               

    # Extract portions
    if "foodPortions" in food_data and food_data['foodPortions']:
        logger.info(f"Portions found for {food_data.get('description')}")
        for portion in food_data['foodPortions']:
            if is_valid_unit(portion.get('measureUnit', {}).get('name')):
                processed_food['portions'].append({
                "description": portion.get('portionDescription'),
                "amount": portion.get('amount'),
                "unit": portion.get('measureUnit', {}).get('name'),
                "gramWeight": portion.get('gramWeight'),
            })
            else:
                # TODO Add code to check if the description is a valid unit
                logger.warning(f"Skipping portion: {portion.get('measureUnit', {}).get('name')}, not a valid unit.")            
    else:
        logger.error(f"No portions found for {food_data.get('description')}")
        # TODO Add code to substitute external source portionData if the FDC data is missing
        return None
    return processed_food

def is_valid_unit(unit_str):
    #  Check if a unit string is a valid Pint unit
    try:
        ureg.parse_expression(unit_str)
        return True
    except (pint.errors.UndefinedUnitError, pint.errors.DimensionalityError):
        return False

def ultra_process_food(ingredient_data):
    """
    Takes a recipe ingredient dictionary with quantity and unit, searches the FoodData Central API for each ingredient, and then calculates the nutrition information for each based on the quantity.

    Input:
    ingredient_data (dict): A dictionary with ingredient names as keys and nested dictionaries as values. 
    Example: {'Flour': {'quantity': '1', 'unit': 'cup'}}

    Output:
    dict: A dictionary with processed food data calculated for a recipe. Strips out unnecessary information and extracts nutrients and portions.
    If no data is found, returns None.
    """
    api_key = get_fdc_api_key()
    if not api_key:
        logger.critical("API key not found. Please set the API key and try again.")
        return None
    
    processed_ingredients = {}
    for ingredient, data in ingredient_data.items():
        logger.info(f"Processing {ingredient}...")
        fdc_id = best_match(ingredient, api_key)
        logger.info(f"Found FDC ID: {fdc_id}")
        food_data = search_food_by_id(fdc_id, api_key)
        logger.info(f"Processing food data for {ingredient}, FDC ID: {fdc_id}")
        processed_food = process_food(food_data)
        logger.info(f"Food Processed. Prepare for {ingredient} ultra processing.")

        # Calculate conversion factor
        ingredient_amount = (data['quantity'], data['unit'])
        logger.info(f"Ingredient amount: {ingredient_amount}")
        conversion_factor = calculate_conversion_factor(processed_food, ingredient_amount)
        logger.info(f"Conversion factor: {conversion_factor}")

        # Begin Ultra Processing
        logger.info(f"Ultra processing {ingredient}...")
        export_to_YAML(processed_food, f"{ingredient}.yaml")
        try:
            ultraprocessed_food = compute_ingredient_nutrition(processed_food, conversion_factor)
            processed_ingredients[ingredient] = ultraprocessed_food
            logger.info(f"Ultra processing complete for {ingredient}.")
        except:
            logger.error(f"Error processing {ingredient}.")
            continue

    return processed_ingredients

def calculate_conversion_factor(processed_food, amount):
    """
    Calculates the conversion factor for a given amount of food based on the portion data.
    
    Inputs:
    processed_food (dict): The processed food data dict
    amount (tuple): A tuple of the format (quantity, unit) for the food.

    Outputs:
    float: The conversion factor to convert the food to the given amount.
    """
    logger.info("Calculating conversion factor...")
    if not processed_food or not amount:
        return None
    
    portions = processed_food.get('portions')
    if not portions:
        # TODO Add a user input section if portions isn't found
        return None
    
    portion = portions[0]
    gram_weight = float(portion.get('gramWeight'))
    logger.debug(f"Gram weight type: {type(gram_weight)}")
    std_qty = portion.get('amount')
    std_unit = portion.get('unit')
    logger.info(f"Standard quantity: {std_qty} {std_unit}")
    logger.info(f"Gram weight: {gram_weight}")

    amt_val = amount[0] * ureg(amount[1])
    try:
        converted_val = amt_val.to(std_unit)
        logger.info(f"Converted value: {converted_val}")
    except:
        logger.error(f"Error converting {amt_val} to {std_unit}")
        return None
    logger.info(f"Converted value magnitude: {converted_val.magnitude}")
    multiplier = float(converted_val.magnitude)
    logger.info(f"Multiplier: {multiplier} Datatype: {type(multiplier)}")
    calculated_conversion_factor = (multiplier * gram_weight) / (std_qty * 100)
    logger.info(f"Calculated conversion factor: {calculated_conversion_factor}")
    return calculated_conversion_factor

def compute_ingredient_nutrition(processed_food, conversion_factor):
    """
    Computes the nutrition information for a given amount of food based on the conversion factor.
    
    Inputs:
    processed_food (dict): The processed food data dict
    conversion_factor (float): This is a multiplier representing the difference in quantity between the standard portion and the desired portion size.

    Outputs:
    dict: A dictionary with the computed nutrition information for the given amount of food.
    """
    if not processed_food or not conversion_factor:
        logger.error("Processed food or conversion factor not found.")
        return None
    
    ultraprocessed_food = {
        "fdcId": processed_food.get('fdcId'),
        "description": processed_food.get('description'),
        "foodCategory": processed_food.get('foodCategory'),
        "nutrients": [],
        "portions": processed_food.get('portions'),
    }

    for nutrient in processed_food.get('nutrients'):
        if nutrient.get('value') is None:
            continue
        else:
            ultraprocessed_food['nutrients'].append({
                "name": nutrient.get('name'),
                "unitName": nutrient.get('unitName'),
                "value": nutrient.get('value') * conversion_factor,
            })
    return ultraprocessed_food

def compute_recipe_nutrition(ultraprocessed_food):
    """
    Computes the nutrition information for a recipe based on the processed ingredient data.
    
    Inputs:
    ultraprocessed_food (dict): A dictionary with processed food data calculated for a recipe.
    
    Outputs:
    dict: A dictionary with the computed nutrition information for the recipe.
    """
    logger.info("Computing recipe nutrition...")
    if not ultraprocessed_food:
        logger.critical("Error: No ultraprocessed food data received.")
        return None
    
    recipe_nutrition = {
        "ingredients": [],
        "totalNutrients": {},
    }

    total_nutrients = {}
    for ingredient, processed_food in ultraprocessed_food.items():
        logger.info(f"Processing {ingredient}...")
        logger.debug(yaml.dump(processed_food, indent=2))
        #logger.debug(yaml.dump(ultraprocessed_food.items(), indent=2))
        try:
            recipe_nutrition['ingredients'].append({
                "name": ingredient,
                "nutrition": processed_food['nutrients'],
            })
            for nutrient in processed_food['nutrients']:
                nutrient_name = nutrient.get('name')
                nutrient_value = nutrient.get('value')
                nutrient_unit = nutrient.get('unitName')
                if nutrient_name in total_nutrients:
                    total_nutrients[nutrient_name]['value'] += nutrient_value
                else:
                    total_nutrients[nutrient_name] = {
                        'value': nutrient_value,
                        'unitName': nutrient_unit,
                    }
            logger.info(f"{ingredient} nutritition appended to recipe nutrition.")
        except:
            logger.error(f"Error processing {ingredient}.")
            continue

    recipe_nutrition['totalNutrients'] = total_nutrients
    logger.info("Recipe nutrition computed.")
    return recipe_nutrition

def main():
        logger.warning("Nutrition Tools Activated.")

        '''Load API key into os.environ'''
        set_api_key.main()

        api_key = get_fdc_api_key()
        if not api_key:
            logger.critical("FDC API key not found. Please set the API key and try again.")
            return

        '''Calculate nutrition for a recipe'''
        ingredients = load_ingredients_from_csv()  # Load recipe from CSV
        ultraprocessed_food = ultra_process_food(ingredients)  # Search and process nutrition information for each ingredient
        try:
            nutrition_facts = compute_recipe_nutrition(ultraprocessed_food)  # Calculate the total nutrition for the recipe
            logger.debug(yaml.dump(nutrition_facts, indent=2))
            export_to_YAML(nutrition_facts, "recipe_nutrition.yaml")
        except:
            logger.critical("Error computing recipe nutrition.")
        
if __name__ == "__main__":
    main()