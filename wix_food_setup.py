"""
Script to create a FoodRecommendations CMS collection on Wix
and populate it with WHO-based food guidance for each child growth status.
"""
import requests
import json
import time

API_KEY = "IST.eyJraWQiOiJQb3pIX2FDMiIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjoie1wiaWRcIjpcIjZlMzg2OTI2LTliZTUtNDhkZi1iN2MzLTdkMjVkMzcyOGRlNlwiLFwiaWRlbnRpdHlcIjp7XCJ0eXBlXCI6XCJhcHBsaWNhdGlvblwiLFwiaWRcIjpcImJjNzA1ZTMzLWY5MGQtNGY3MS1iODE0LTA4OGRmZjQyZmQ4N1wifSxcInRlbmFudFwiOntcInR5cGVcIjpcImFjY291bnRcIixcImlkXCI6XCJlOGYzNGUyZS0xYjczLTQwYzktYTJkMS1kMDVmMjNiNzM4YjNcIn19IiwiaWF0IjoxNzcxMzM3NDQ0fQ.aMJeqjxr6HtrEOmGWMx17qRS8VbN4iLFEuufT1rZ24nykEQFQFjWAEN9zE11JKRbRwqEYf_CTekYfXZObaNjgE_jxEp1-Lf1LAS56mq2IBkbKE7-M-o-r6cbwNtGqeYcOOHLeuEjDokvsnbSry6fctQbfhvaC_F4e3peTCB4lo9GyzDhuAe4d0FRHv8hQPkFlEARV-m0_0IbXP-C1h1_zGWRdzCoBVT0Iqd-1-KvwSvVAtwcBZjyxYibEcNA0vwLPORtBjT-2wfoqQ1J8jr41nlszegbgGq5r7FlpTIh1dnzU0RgiF0LwRGisDQTqAMEW60cRupOH6d_DB8bJF5j4A"
SITE_ID = "d0fa869a-cbdb-4975-8a29-d01f7a7c1245"
HEADERS = {
    "Authorization": API_KEY,
    "wix-site-id": SITE_ID,
    "Content-Type": "application/json",
}

COLLECTION_ID = "FoodRecommendations"


# ── Step 1: Create collection ──────────────────────────────────
def create_collection():
    url = "https://www.wixapis.com/wix-data/v2/collections"
    body = {
        "collection": {
            "id": COLLECTION_ID,
            "displayName": "Food Recommendations",
            "fields": [
                {"key": "status",           "displayName": "Status",            "type": "TEXT"},
                {"key": "goal",             "displayName": "Goal",              "type": "TEXT"},
                {"key": "recommendedFoods", "displayName": "Recommended Foods", "type": "TEXT"},
                {"key": "mealPattern",      "displayName": "Meal Pattern",      "type": "TEXT"},
                {"key": "snackIdeas",       "displayName": "Snack Ideas",       "type": "TEXT"},
                {"key": "avoid",            "displayName": "Avoid",             "type": "TEXT"},
                {"key": "activityTip",      "displayName": "Activity / Tip",    "type": "TEXT"},
                {"key": "keyNutrients",     "displayName": "Key Nutrients",     "type": "TEXT"},
                {"key": "category",         "displayName": "Category",          "type": "TEXT"},
                {"key": "sortOrder",        "displayName": "Sort Order",        "type": "NUMBER"},
            ],
        }
    }
    r = requests.post(url, headers=HEADERS, json=body)
    if r.status_code in (200, 201):
        print(f"OK - Collection '{COLLECTION_ID}' created successfully!")
        return True
    elif r.status_code == 409 or "already exists" in r.text.lower():
        print(f"OK - Collection '{COLLECTION_ID}' already exists — will insert items into it.")
        return True
    else:
        print(f"ERROR - Failed to create collection: {r.status_code}")
        print(r.text[:500])
        return False


# ── Step 2: Insert data items ──────────────────────────────────
def insert_item(data: dict):
    url = "https://www.wixapis.com/wix-data/v2/items"
    body = {
        "dataCollectionId": COLLECTION_ID,
        "dataItem": {"data": data},
    }
    r = requests.post(url, headers=HEADERS, json=body)
    if r.status_code in (200, 201):
        title = data.get("status") or data.get("title", "item")
        print(f"  OK - Inserted: {title}")
        return True
    else:
        print(f"  ERROR - Failed ({r.status_code}): {r.text[:300]}")
        return False


def populate_status_recommendations():
    """Insert 5 status-based food recommendation items."""
    items = [
        {
            "status": "Underweight",
            "category": "Status-Based",
            "sortOrder": 1,
            "goal": "Healthy weight gain through calorie-dense, nutrient-rich foods",
            "recommendedFoods": "🥛 Whole milk | 🧀 Cheese & Paneer | 🥚 Eggs | 🥜 Peanut butter | 🍌 Bananas | 🥑 Avocado | 🍠 Sweet potato | 🌰 Nuts (crushed)",
            "mealPattern": "HOW TO EAT: Offer 5-6 small meals/snacks instead of 3 large meals. Add one calorie booster per meal (ghee, nut powder, cheese). Do not give excess water before meals. Track weight monthly.\n\nMEAL IDEAS: Banana milkshake with full-fat milk | Dry fruits ladoo with ghee | Cheese toast with butter | Sooji halwa with ghee | Makhana with ghee",
            "snackIdeas": "Dry fruits ladoo | Banana milkshake | Cheese toast | Sooji halwa | Makhana with ghee | Ragi porridge | Dal khichdi with ghee",
            "avoid": "Junk food that fills stomach without nutrition; excessive water before meals; low-calorie snacks",
            "activityTip": "Monitor weight monthly; consult pediatrician if no weight gain in 2 months; light play, no vigorous exercise",
            "keyNutrients": "Calories, healthy fats, protein, iron, calcium",
        },
        {
            "status": "Healthy",
            "category": "Status-Based",
            "sortOrder": 2,
            "goal": "Maintain balanced growth with nutritious, varied diet",
            "recommendedFoods": "🍎 Seasonal fruits | 🥗 Vegetables | 🫘 Dal/Lentils | 🥛 Milk & Yogurt | 🍚 Rice & Roti | 🥚 Eggs | 🐟 Fish | 🌾 Whole grains",
            "mealPattern": "HOW TO EAT: 3 meals + 2 healthy snacks per day at consistent times. Use balanced plate: 1/2 vegetables-fruits, 1/4 protein, 1/4 grains. Family meals without pressure feeding. Child decides their own appetite.\n\nMEAL IDEAS: Fresh fruit slices | Sprouts chaat | Idli with sambar | Poha (flattened rice) | Curd with fruits | Boiled egg",
            "snackIdeas": "Fresh fruit | Sprouts chaat | Idli | Poha | Curd with fruits | Boiled egg | Whole grain toast with curd",
            "avoid": "Excessive sugary snacks, processed foods, sugary drinks; maintain moderation",
            "activityTip": "60+ minutes active outdoor play daily; regular pediatric check-ups every 6 months; encourage sports or dance",
            "keyNutrients": "Balanced macros — protein, carbs, healthy fats, vitamins, minerals",
        },
        {
            "status": "Overweight",
            "category": "Status-Based",
            "sortOrder": 3,
            "goal": "Slow weight gain while height catches up; improve food quality",
            "recommendedFoods": "🥒 Vegetables | 🍎 Fruits | 🐔 Lean proteins (chicken, fish) | 🫘 Dal & lentils | 🌾 Whole grains | 🥛 Low-fat milk | 🥗 Salads",
            "mealPattern": "HOW TO EAT: Serve fixed portions using a small plate; avoid second servings. Use water first, then meal; avoid screen-time eating. Eat slowly and chew well; stop when satisfied. 60 minutes active play daily with regular sleep schedule.\n\nMEAL IDEAS: Vegetable soup + whole wheat bread | Grilled fish/chicken with salad | Dal with brown rice | Fruit chaat | Sprout salad",
            "snackIdeas": "Cucumber sticks | Buttermilk | Roasted chana | Fruit salad | Plain popcorn | Carrot sticks | Tomato slices",
            "avoid": "Sugary drinks (juice, soda), fried foods, biscuits, chips, white bread, maida, excess oil/ghee, fast food",
            "activityTip": "60 minutes daily physical activity (cycling, running, swimming); limit screen time; family activities; do NOT put child on restrictive diet — focus on food quality",
            "keyNutrients": "Fiber, lean protein, complex carbohydrates, vitamins, minerals",
        },
        {
            "status": "Obese",
            "category": "Status-Based",
            "sortOrder": 4,
            "goal": "Gradual weight management under pediatric supervision",
            "recommendedFoods": "🌱 High-fiber vegetables | 🫘 Lentils & legumes | 🐟 Lean protein | 🌾 Oats & whole wheat | 🥗 Salads | 🍲 Dal soup | 🍗 Grilled fish/chicken",
            "mealPattern": "HOW TO EAT: Smaller portions using a small plate; never serve second helpings. Eat slowly and chew well; drink water before meals. Family meals at table, not in front of TV. Establish fixed meal times. 60+ minutes daily activity; limit screen time to <1 hour.\n\nMEAL IDEAS: Vegetable soup + whole wheat roti | Grilled chicken with steamed broccoli | Dal with brown rice | Salad with lemon dressing | Sprout chaat",
            "snackIdeas": "Sprout salad | Roasted makhana (plain) | Vegetable sticks | Buttermilk | Fruit (no added sugar) | Cucumber | Tomato",
            "avoid": "Sugar-sweetened beverages, fast food, packaged snacks, excess ghee/oil, white rice, sweets, sugary cereals, fried snacks",
            "activityTip": "60+ minutes daily activity (walking, cycling, swimming, sports); family-based lifestyle changes most effective; MANDATORY pediatric consultation for monitoring; never use restrictive diets",
            "keyNutrients": "Fiber, lean protein, low glycemic carbs, plenty of water, minerals",
        },
        {
            "status": "Stunted",
            "category": "Status-Based",
            "sortOrder": 5,
            "goal": "Support linear (height) growth through micronutrient-rich foods",
            "recommendedFoods": "🥚 Eggs | 🐟 Fish & liver | 🌿 Green leafy vegetables (spinach, methi) | 🍚 Fortified cereals | 🧀 Paneer & curd | 🫘 Soybean | 🌾 Ragi",
            "mealPattern": "HOW TO EAT: Keep regular meal times; include protein in EVERY meal. Breakfast: egg + ragi porridge + milk. Lunch/Dinner: dal/paneer/fish + vegetable + roti/rice. Pair iron foods with vitamin C foods (lemon, orange, guava). 3 meals + 2 protein-rich snacks daily.\n\nMEAL IDEAS: Boiled egg with ragi porridge | Paneer curry with spinach & roti | Fish with orange lentils | Soybean dal with whole wheat roti | Banana with peanut butter",
            "snackIdeas": "Boiled egg | Paneer cubes | Peanut chikki | Ragi porridge | Banana with peanut butter | Sprout chaat | Curd",
            "avoid": "Empty-calorie foods (junk, sugary snacks); excess tea/coffee (blocks iron absorption); processed foods",
            "activityTip": "Pediatric evaluation for iron/zinc/vitamin A supplements; stunting from chronic undernutrition—consistent diet improvements over 3-6 months show results; regular monitoring essential",
            "keyNutrients": "🔴 Iron (spinach, liver, jaggery) | 🔵 Zinc (pumpkin seeds, chickpeas) | 🟡 Vitamin A (carrots, mango, sweet potato) | 🟢 Calcium (milk, ragi) | ⚪ Protein",
        },
    ]

    print("\nInserting status-based food recommendations...")
    for item in items:
        insert_item(item)
        time.sleep(0.3)


def populate_age_guide():
    """Insert age-based feeding guide items."""
    items = [
        {
            "status": "0-6 Months",
            "category": "Age-Based Guide",
            "sortOrder": 10,
            "goal": "Exclusive breastfeeding — no water, no other food needed",
            "recommendedFoods": "Breast milk only (or formula if medically advised)",
            "mealPattern": "On-demand feeding, 8-12 times per day",
            "snackIdeas": "Not applicable at this age",
            "avoid": "Water, honey, solid foods, cow's milk, fruit juice",
            "activityTip": "Tummy time for development; regular weight monitoring",
            "keyNutrients": "All nutrients provided by breast milk",
        },
        {
            "status": "6-8 Months",
            "category": "Age-Based Guide",
            "sortOrder": 11,
            "goal": "Introduce complementary foods alongside breastfeeding",
            "recommendedFoods": "Mashed/pureed foods — rice cereal, mashed banana, boiled & mashed potato, dal water, apple puree, suji kheer",
            "mealPattern": "2-3 meals per day + breast milk; start with 2-3 tablespoons, gradually increase",
            "snackIdeas": "Mashed banana, boiled carrot puree, rice porridge",
            "avoid": "Honey, salt, sugar, whole nuts, cow's milk as main drink",
            "activityTip": "Introduce one new food at a time; wait 3 days before trying another to watch for allergies",
            "keyNutrients": "Iron-fortified cereals, vitamin C-rich fruits to aid iron absorption",
        },
        {
            "status": "9-12 Months",
            "category": "Age-Based Guide",
            "sortOrder": 12,
            "goal": "Expand food variety with soft, chopped textures",
            "recommendedFoods": "Soft chopped foods, finger foods — khichdi, dalia, soft idli, mashed egg, small pieces of soft fruit, paneer cubes",
            "mealPattern": "3 meals + 1 snack per day + breast milk",
            "snackIdeas": "Soft fruit pieces, cheese cubes, rusk, small roti pieces with dal",
            "avoid": "Honey (till 12 months), choking hazards (whole grapes, nuts, popcorn), added salt/sugar",
            "activityTip": "Let baby self-feed with fingers to develop motor skills; continue breastfeeding",
            "keyNutrients": "Protein (egg, dal), Iron, Zinc, Calcium",
        },
        {
            "status": "1-2 Years",
            "category": "Age-Based Guide",
            "sortOrder": 13,
            "goal": "Transition to family foods with appropriate textures",
            "recommendedFoods": "Family foods — roti, rice, dal, vegetables, fruits, whole milk, curd, egg, fish, chicken (if non-veg)",
            "mealPattern": "3 meals + 2 snacks per day; offer variety at each meal",
            "snackIdeas": "Fruit slices, cheese toast, ragi dosa, boiled egg, curd with mashed fruit",
            "avoid": "Choking hazards, excess sugar/salt, packaged juices, junk food",
            "activityTip": "Encourage self-feeding with spoon; establish regular meal times; whole milk (not low-fat) at this age",
            "keyNutrients": "Protein, calcium, iron, healthy fats, vitamins A & D",
        },
        {
            "status": "2-5 Years",
            "category": "Age-Based Guide",
            "sortOrder": 14,
            "goal": "Balanced plate — build healthy eating habits for life",
            "recommendedFoods": "Cereal/grain + protein + vegetable + fruit + dairy at each meal; roti, rice, dal, paneer, eggs, seasonal vegetables, fruits, milk, curd",
            "mealPattern": "3 meals + 2 healthy snacks per day; family meals together",
            "snackIdeas": "Sprout chaat, peanut butter toast, fruit smoothie, vegetable paratha, idli, poha",
            "avoid": "Sugary cereals, candy, chips, soda, excessive screen-time snacking",
            "activityTip": "60+ minutes active play daily; involve children in food preparation; make meals colorful and fun",
            "keyNutrients": "Balanced macros, fiber, iron, calcium, vitamin D, omega-3 (from fish/walnuts)",
        },
    ]

    print("\nInserting age-based feeding guide...")
    for item in items:
        insert_item(item)
        time.sleep(0.3)


# ── Main ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Wix Food Recommendations Setup")
    print("=" * 60)

    # Step 1: List existing collections
    print("\nChecking existing collections...")
    r = requests.get("https://www.wixapis.com/wix-data/v2/collections", headers=HEADERS)
    if r.ok:
        for c in r.json().get("collections", []):
            print(f"  - {c.get('id')} ({c.get('displayName', '')})")
    else:
        print(f"  Could not list collections: {r.status_code}")

    # Step 2: Create collection
    print(f"\nCreating collection '{COLLECTION_ID}'...")
    if not create_collection():
        print("Trying to insert items anyway (collection may already exist)...")

    # Step 3: Insert items
    populate_status_recommendations()
    populate_age_guide()

    print("\n" + "=" * 60)
    print("  DONE! 10 items added to Wix CMS.")
    print("  Go to Wix Editor -> CMS -> FoodRecommendations to see them.")
    print("  Connect this collection to your Food Recommendation page.")
    print("=" * 60)
