import pandas as pd
import requests
import re
import os

GLOBAL_DEEP_COUNTER = 0
GLOBAL_MAX_DEEP_COUNTER = 5


def get_entities_by_query(query):
    params = {
        "action": "wbsearchentities",
        "language": "en",
        "format": "json",
        "search": query
    }
    url = "https://www.wikidata.org/w/api.php"
    return requests.get(url, params).json()


def get_categories(query):
    params = {
        "action": "query",
        "titles": query,
        "format": "json",
        "prop": "categories",
        "clprop": "hidden",
        "cllimit": 500
    }
    url = "https://en.wikipedia.org/w/api.php"
    json_object = requests.get(url, params).json()
    pages = json_object["query"]["pages"]
    json_object_categories = []
    for item in pages.values():
        if "categories" not in item:
            return json_object_categories
        for cat in item["categories"]:
            if "hidden" not in cat:
                json_object_categories.append(cat["title"])
    return json_object_categories


def get_deeper_categories(category_list):
    next_level_categories = []
    for category in category_list:
        received_categories = get_categories(category)
        next_level_categories = next_level_categories + received_categories
    return list(set(next_level_categories))


def get_objects_common_categories(object_categories):
    flat_categories = []
    for row in object_categories:
        row_all_categories = []
        for category_level in row:
            row_all_categories = row_all_categories + category_level
        flat_categories.append(set(row_all_categories))
    common_categories = recurrent_sets_intersection(flat_categories)
    return common_categories


def recurrent_sets_intersection(sets_list):
    current_set = sets_list[0]
    if len(sets_list) == 1:
        return current_set
    return current_set.intersection(recurrent_sets_intersection(sets_list[1:]))


def celebrate_success(categories):
    print("Found category that fits to all the rows!")
    print(categories)


def prepare_new_list_of_lists(list):
    new_list = []
    for index in range(len(list)):
        new_list.append([])
        new_list[index].append([list[index]])
    return new_list


def filter_aggregation_categories(list):
    pattern = ".* by (country|place|nationality|city)"
    result = [string for string in list if not re.match(pattern, string, flags=0)]
    if len(result) > 0:
        return result
    else:
        return list


def get_list_common_categories(object_categories):
    global GLOBAL_DEEP_COUNTER
    global GLOBAL_MAX_DEEP_COUNTER

    GLOBAL_DEEP_COUNTER += 1
    if GLOBAL_DEEP_COUNTER > GLOBAL_MAX_DEEP_COUNTER:
        print("STOPPED BY GLOBAL DEPTH COUNTER")
        return None

    deep_counter = 0
    max_deep_counter = 5

    while deep_counter < max_deep_counter:
        deep_counter += 1
        for x in range(len(object_categories)):
            last_categories = object_categories[x][-1]
            new_categories = []
            for cat in last_categories:
                new_categories = new_categories + get_categories(cat)
            object_categories[x].append(list(set(new_categories)))
        result = get_objects_common_categories(object_categories)
        if (len(result)) > 0:
            filtered_results = filter_aggregation_categories(list(result))
            if len(filtered_results) == 1:
                return filtered_results
            else:
                return get_list_common_categories(prepare_new_list_of_lists(filtered_results))

    print("STOPPED BY LOCAL DEPTH COUNTER")
    return None


def save_to_file(filename, result):
    to_save = result
    if result is None:
        to_save = "Not found"
    file = open("results/" + filename + ".txt", "w+")
    file.write(str(to_save))
    file.close()


def run_script_for_file(filename):
    df = pd.read_csv('tables/' + filename, usecols=['col0'])
    object_categories = []

    # init first-level categories
    for index, row in df.iterrows():
        if len(get_categories(row['col0'])) > 0:
            object_categories.append([[row['col0']]])

    result = get_list_common_categories(object_categories)
    if result is None:
        print("Category not found :/")
    else:
        print("Category found! It is: ")
        print(result)
    save_to_file(filename, result)


def main():
    files = os.listdir("tables/")
    global GLOBAL_DEEP_COUNTER
    for index in range(len(files)):
        GLOBAL_DEEP_COUNTER = 0
        filename = files[index]
        print("[" + str(index) + "/" + str(len(files)) + "] Running script for " + filename)
        try:
            run_script_for_file(filename)
        except:
            print("Error!")
            save_to_file(filename, "Error!")


main()
