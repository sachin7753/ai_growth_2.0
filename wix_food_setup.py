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
        print(f"✅ Collection '{COLLECTION_ID}' created successfully!")
        return True
    elif r.status_code == 409 or "already exists" in r.text.lower():
        print(f"⚠️  Collection '{COLLECTION_ID}' already exists — will insert items into it.")
        return True
    else:
        print(f"❌ Failed to create collection: {r.status_code}")
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
        print(f"  ✅ Inserted: {title}")
        return True
    else:
        print(f"  ❌ Failed ({r.status_code}): {r.text[:300]}")
        return False


def populate_status_recommendations():
    """Insert 5 status-based food recommendation items."""
    items = [
        {
            "status": "Underweight",
            "category": "Status-Based",
            "sortOrder": 1,
            "goal": "Healthy weight gain through calorie-dense, nutrient-rich foods",
            "recommendedFoods": "Whole milk, cheese, paneer, eggs, ghee, peanut butter, bananas, avocado, ragi porridge, dal khichdi, sweet potato, nuts",
            "mealPattern": "5-6 small meals per day instead of 3 large ones",
            "snackIdeas": "Dry fruits ladoo, banana milkshake, cheese toast, sooji halwa, makhana with ghee",
            "avoid": "Junk food that fills stomach without nutrition; excessive water before meals",
            "activityTip": "Monitor weight monthly; consult pediatrician if no weight gain in 2 months",
            "keyNutrients": "Calories, healthy fats, protein, iron, calcium",
        },
        {
            "status": "Healthy",
            "category": "Status-Based",
            "sortOrder": 2,
            "goal": "Maintain balanced growth with nutritious, varied diet",
            "recommendedFoods": "Seasonal fruits, vegetables, dal/lentils, milk, curd, roti, rice, eggs, fish, whole grains",
            "mealPattern": "3 meals + 2 healthy snacks per day",
            "snackIdeas": "Fresh fruit, sprouts chaat, idli, poha, curd with fruits, boiled egg",
            "avoid": "Excessive sugary snacks, processed foods; maintain moderation",
            "activityTip": "60+ minutes active outdoor play daily; regular pediatric check-ups every 6 months",
            "keyNutrients": "Balanced macros — protein, carbs, healthy fats, vitamins, minerals",
        },
        {
            "status": "Overweight",
            "category": "Status-Based",
            "sortOrder": 3,
            "goal": "Slow weight gain while height catches up; improve food quality",
            "recommendedFoods": "Vegetables, fruits, lean proteins (chicken, fish, dal), whole grains, low-fat milk, salads",
            "mealPattern": "3 controlled-portion meals + 1-2 light snacks; eat slowly, chew well",
            "snackIdeas": "Cucumber sticks, buttermilk, roasted chana, fruit salad, plain popcorn",
            "avoid": "Sugary drinks (juice, soda), fried foods, biscuits, chips, white bread, maida, excess oil/ghee",
            "activityTip": "60 minutes daily physical activity (cycling, running, swimming); never put a child on a restrictive 'diet' — focus on food quality",
            "keyNutrients": "Fiber, lean protein, complex carbohydrates, vitamins",
        },
        {
            "status": "Obese",
            "category": "Status-Based",
            "sortOrder": 4,
            "goal": "Gradual weight management under pediatric supervision",
            "recommendedFoods": "High-fiber vegetables, lentils, lean protein, oats, whole wheat roti, salads, dal soup, grilled fish/chicken",
            "mealPattern": "Smaller portions, no second servings, eat slowly; drink water before meals",
            "snackIdeas": "Sprout salad, plain roasted makhana, vegetable sticks with hummus, buttermilk",
            "avoid": "Sugar-sweetened beverages, fast food, packaged snacks, excess ghee/oil, white rice in excess, sweets",
            "activityTip": "60+ minutes daily activity; limit screen time to under 1 hour; mandatory pediatric consultation; family-based lifestyle changes work best",
            "keyNutrients": "Fiber, protein, low glycemic carbs, plenty of water",
        },
        {
            "status": "Stunted",
            "category": "Status-Based",
            "sortOrder": 5,
            "goal": "Support linear (height) growth through micronutrient-rich foods",
            "recommendedFoods": "Eggs, fish, liver, green leafy vegetables (spinach, methi), fortified cereals, curd, paneer, soybean, ragi",
            "mealPattern": "Ensure protein in every meal — dal, paneer, eggs, soybean; 3 meals + 2 protein-rich snacks",
            "snackIdeas": "Boiled egg, paneer cubes, peanut chikki, ragi porridge, banana with peanut butter",
            "avoid": "Empty-calorie foods that displace nutrient-rich foods; excess tea/coffee (blocks iron absorption)",
            "activityTip": "Pediatric evaluation for iron/zinc/vitamin A supplements; stunting results from chronic undernutrition — consistent diet changes over months are key",
            "keyNutrients": "Iron (spinach, jaggery), Zinc (pumpkin seeds, chickpeas), Vitamin A (carrots, mango, sweet potato), Calcium (milk, ragi), Protein",
        },
    ]

    print("\n📋 Inserting status-based food recommendations...")
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

    print("\n📋 Inserting age-based feeding guide...")
    for item in items:
        insert_item(item)
        time.sleep(0.3)


# ── Main ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Wix Food Recommendations Setup")
    print("=" * 60)

    # Step 1: List existing collections
    print("\n📂 Checking existing collections...")
    r = requests.get("https://www.wixapis.com/wix-data/v2/collections", headers=HEADERS)
    if r.ok:
        for c in r.json().get("collections", []):
            print(f"  - {c.get('id')} ({c.get('displayName', '')})")
    else:
        print(f"  Could not list collections: {r.status_code}")

    # Step 2: Create collection
    print(f"\n📦 Creating collection '{COLLECTION_ID}'...")
    if not create_collection():
        print("Trying to insert items anyway (collection may already exist)...")

    # Step 3: Insert items
    populate_status_recommendations()
    populate_age_guide()

    print("\n" + "=" * 60)
    print("  ✅ Done! 10 items added to Wix CMS.")
    print("  Go to Wix Editor → CMS → FoodRecommendations to see them.")
    print("  Connect this collection to your Food Recommendation page.")
    print("=" * 60)
