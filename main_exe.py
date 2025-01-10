import requests
import json
import os

# Constants
CACHE_FILE = "gw2_cache.json"

# Function to load cache
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

# Function to save cache
def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Function to find characters by item name
def find_character_by_item(item_name, all_items):
    matches = [entry for entry in all_items if entry["item"].lower() == item_name.lower()]
    return matches if matches else f"No character has the item '{item_name}'."

# Main script
api_key = input("What is your API key: ")
print("Your API key is {}.".format(api_key))

# Load cache
cache = load_cache()

# Check if data already exists in cache
if "all_items" in cache:
    print("Using cached data.")
    all_items = cache["all_items"]
else:
    # API URLs
    characters_url = f"https://api.guildwars2.com/v2/characters?access_token={api_key}"
    base_character_inventory_url = "https://api.guildwars2.com/v2/characters/{character}/inventory?access_token={api_key}"
    item_details_url = "https://api.guildwars2.com/v2/items?ids={ids}"

    # Fetch character names
    characters_response = requests.get(characters_url)

    if characters_response.status_code == 200:
        characters = characters_response.json()
        print(f"Found {len(characters)} characters.")

        all_items = []  # List to store all items across all characters

        for character in characters:
            print(f"\nFetching inventory for: {character}")
            character_inventory_url = base_character_inventory_url.format(character=character.replace(" ", "%20"), api_key=api_key)
            inventory_response = requests.get(character_inventory_url)

            if inventory_response.status_code == 200:
                inventory_data = inventory_response.json()
                bags = inventory_data.get("bags", [])

                for bag in bags:
                    if not bag:
                        continue

                    # Fetch bag name
                    bag_id = bag["id"]
                    bag_details_response = requests.get(f"https://api.guildwars2.com/v2/items/{bag_id}")
                    bag_name = "Unknown Bag"
                    if bag_details_response.status_code == 200:
                        bag_name = bag_details_response.json().get("name", "Unknown Bag")
                    print(f"Bag: {bag_name} (ID: {bag_id}), Size: {bag['size']}")

                    # Gather item IDs for bulk fetching
                    item_ids = [item["id"] for item in bag.get("inventory", []) if item]
                    item_counts = {item["id"]: item["count"] for item in bag.get("inventory", []) if item}

                    # Fetch item details in bulk
                    if item_ids:
                        items_response = requests.get(item_details_url.format(ids=",".join(map(str, item_ids))))
                        if items_response.status_code == 200:
                            items_data = items_response.json()
                            for item in items_data:
                                item_name = item.get("name", "Unknown Item")
                                item_id = item["id"]
                                count = item_counts.get(item_id, 1)
                                print(f"  - {item_name} x{count} (ID: {item_id})")
                                all_items.append({"character": character, "bag": bag_name, "item": item_name, "count": count})
                        else:
                            print(f"Error fetching items: {items_response.status_code}")
            else:
                print(f"Error fetching inventory for {character}: {inventory_response.status_code}")

        # Save to cache
        cache["all_items"] = all_items
        save_cache(cache)
        print("\nFinished fetching all items.")
    else:
        print(f"Error fetching character list: {characters_response.status_code}")
        exit()

# Loop for searching items
while True:
    search_item = input("\nEnter the name of the item to search for (or type 'exit' to quit): ").strip()
    if search_item.lower() == "exit":
        print("Exiting item search.")
        break
    search_result = find_character_by_item(search_item, all_items)
    if isinstance(search_result, list):
        for match in search_result:
            print(f"{match['item']} is with {match['character']} in {match['bag']}, Quantity: {match['count']}.")
    else:
        print(search_result)
