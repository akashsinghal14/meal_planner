import streamlit as st
import openai
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {}
    if "meal_plan" not in st.session_state:
        st.session_state.meal_plan = {}
    if "profile_completed" not in st.session_state:
        st.session_state.profile_completed = False
    if "grocery_list" not in st.session_state:
        st.session_state.grocery_list = {}
    if "prep_reminders" not in st.session_state:
        st.session_state.prep_reminders = {}
    if "grocery_checked" not in st.session_state:
        st.session_state.grocery_checked = {}
    if "prep_completed" not in st.session_state:
        st.session_state.prep_completed = {}

def get_openai_response(messages, user_context=""):
    """Get response from OpenAI API with user context"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create system message with user context
        system_message = f"""You are a helpful AI assistant specializing in meal planning and cooking advice. 
        
        User Profile Context:
        {user_context}
        
        Use this information to provide personalized recommendations. Always consider the user's dietary restrictions, preferences, and health goals when suggesting meals or recipes."""
        
        full_messages = [{"role": "system", "content": system_message}] + messages
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=full_messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def generate_meal_plan(user_profile):
    """Generate a 7-day meal plan based on user profile"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        profile_text = format_user_profile_for_ai(user_profile)
        
        prompt = f"""Create a 7-day meal plan based on this user profile:

{profile_text}

CRITICAL REQUIREMENTS:
1. MAXIMUM VARIETY - NO REPETITIVE MEALS across all 7 days
2. Use DIFFERENT protein sources each day (chicken, fish, beef, tofu, eggs, legumes, etc.)
3. Vary cooking methods (grilled, baked, stir-fried, steamed, raw, etc.)
4. Include diverse cuisines (Mediterranean, Asian, Mexican, Indian, American, etc.)
5. Make each breakfast unique (oats, eggs, smoothies, pancakes, avocado toast, etc.)
6. Creative and different snacks each day
7. Respond with ONLY valid JSON. No extra text, no markdown, no explanations.

JSON format:
{{
  "Monday": {{
    "breakfast": {{
      "meal": "creative specific description", 
      "ingredients": ["ingredient1", "ingredient2", "ingredient3", "ingredient4"], 
      "prep_notes": "detailed advance preparation timing",
      "calories": 350, "protein": 15, "carbs": 45, "fat": 12, "fiber": 6
    }},
    "lunch": {{
      "meal": "unique cuisine-inspired description", 
      "ingredients": ["ingredient1", "ingredient2", "ingredient3", "ingredient4"], 
      "prep_notes": "specific prep timing and methods",
      "calories": 450, "protein": 25, "carbs": 55, "fat": 15, "fiber": 8
    }},
    "dinner": {{
      "meal": "diverse protein and cooking method", 
      "ingredients": ["ingredient1", "ingredient2", "ingredient3", "ingredient4"], 
      "prep_notes": "marinating, overnight prep details",
      "calories": 500, "protein": 30, "carbs": 50, "fat": 18, "fiber": 10
    }},
    "snack1": {{
      "meal": "creative healthy snack", 
      "ingredients": ["ingredient1", "ingredient2"], 
      "prep_notes": "preparation method and timing",
      "calories": 150, "protein": 8, "carbs": 15, "fat": 6, "fiber": 3
    }},
    "snack2": {{
      "meal": "different style snack", 
      "ingredients": ["ingredient1", "ingredient2"], 
      "prep_notes": "specific prep notes",
      "calories": 120, "protein": 5, "carbs": 12, "fat": 4, "fiber": 2
    }}
  }},
  "Tuesday": {{...completely different meals...}},
  "Wednesday": {{...totally unique options...}},
  "Thursday": {{...new flavors and styles...}},
  "Friday": {{...diverse international options...}},
  "Saturday": {{...weekend special meals...}},
  "Sunday": {{...comfort food variety...}}
}}

VARIETY EXAMPLES:
- Breakfasts: overnight oats, scrambled eggs, chia pudding, avocado toast, smoothie bowl, protein pancakes, omelet
- Proteins: salmon, chicken breast, tofu, turkey, beef, fish, legumes, eggs
- Cuisines: Italian pasta, Asian stir-fry, Mexican bowl, Mediterranean, Indian curry, American grill
- Prep methods: marinating overnight, soaking grains, defrosting proteins, chopping vegetables night before

Include detailed prep notes with specific timing. Respect dietary restrictions and preferences."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=3000
        )
        
        # Try to parse JSON response
        try:
            response_content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_content.startswith("```json"):
                response_content = response_content[7:]
            elif response_content.startswith("```"):
                response_content = response_content[3:]
            
            if response_content.endswith("```"):
                response_content = response_content[:-3]
            
            # Clean up the response
            response_content = response_content.strip()
            
            # Find JSON object boundaries
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_content = response_content[start_idx:end_idx+1]
                
                # Additional cleaning - fix common JSON issues
                json_content = json_content.replace('\n', ' ')
                json_content = json_content.replace('\t', ' ')
                # Fix multiple spaces
                import re
                json_content = re.sub(r'\s+', ' ', json_content)
                
                meal_plan = json.loads(json_content)
                return meal_plan
            else:
                return {"error": "Could not find valid JSON in response", "raw_response": response_content}
                
        except json.JSONDecodeError as e:
            # If JSON parsing still fails, try a fallback approach
            return generate_fallback_meal_plan(user_profile, response.choices[0].message.content, str(e))
            
    except Exception as e:
        return {"error": f"Failed to generate meal plan: {str(e)}"}

def generate_fallback_meal_plan(user_profile, raw_response, error_msg):
    """Generate a simple fallback meal plan when JSON parsing fails"""
    try:
        # Create diverse meal plans for each day
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        fallback_plan = {}
        
        # Define diverse meals for each day
        daily_meals = {
            "Monday": {
                "breakfast": {
                    "meal": "Overnight oats with fruits and nuts",
                    "ingredients": ["rolled oats", "banana", "almonds", "blueberries", "milk", "honey"],
                    "prep_notes": "Mix oats with milk and honey the night before, refrigerate overnight",
                    "calories": 350, "protein": 12, "carbs": 45, "fat": 10, "fiber": 8
                },
                "lunch": {
                    "meal": "Grilled chicken Caesar salad",
                    "ingredients": ["chicken breast", "romaine lettuce", "parmesan cheese", "croutons", "caesar dressing"],
                    "prep_notes": "Marinate chicken with herbs overnight, prepare salad components",
                    "calories": 450, "protein": 30, "carbs": 25, "fat": 15, "fiber": 6
                },
                "dinner": {
                    "meal": "Baked salmon with quinoa and roasted vegetables",
                    "ingredients": ["salmon fillet", "quinoa", "broccoli", "bell peppers", "olive oil", "lemon"],
                    "prep_notes": "Rinse quinoa thoroughly, marinate salmon for 30 minutes",
                    "calories": 520, "protein": 35, "carbs": 42, "fat": 18, "fiber": 7
                },
                "snack1": {"meal": "Greek yogurt with berries", "ingredients": ["Greek yogurt", "mixed berries", "honey"], "prep_notes": "Use chilled yogurt", "calories": 150, "protein": 10, "carbs": 15, "fat": 5, "fiber": 3},
                "snack2": {"meal": "Apple with almond butter", "ingredients": ["apple", "almond butter"], "prep_notes": "Slice apple fresh", "calories": 120, "protein": 4, "carbs": 12, "fat": 8, "fiber": 4}
            },
            "Tuesday": {
                "breakfast": {
                    "meal": "Scrambled eggs with whole grain toast",
                    "ingredients": ["eggs", "whole grain bread", "spinach", "tomatoes", "olive oil"],
                    "prep_notes": "Use fresh eggs at room temperature for fluffier scramble",
                    "calories": 340, "protein": 18, "carbs": 30, "fat": 14, "fiber": 5
                },
                "lunch": {
                    "meal": "Mediterranean bowl with hummus",
                    "ingredients": ["chickpeas", "cucumber", "tomatoes", "feta cheese", "olive oil", "pita bread"],
                    "prep_notes": "Soak chickpeas overnight if using dried ones",
                    "calories": 480, "protein": 18, "carbs": 55, "fat": 20, "fiber": 12
                },
                "dinner": {
                    "meal": "Stir-fried tofu with brown rice",
                    "ingredients": ["firm tofu", "brown rice", "broccoli", "carrots", "soy sauce", "ginger"],
                    "prep_notes": "Press tofu overnight to remove moisture, cook brown rice in advance",
                    "calories": 490, "protein": 20, "carbs": 60, "fat": 15, "fiber": 8
                },
                "snack1": {"meal": "Smoothie bowl", "ingredients": ["banana", "spinach", "protein powder", "granola"], "prep_notes": "Freeze banana overnight", "calories": 180, "protein": 12, "carbs": 25, "fat": 4, "fiber": 6},
                "snack2": {"meal": "Hummus with vegetables", "ingredients": ["hummus", "carrots", "celery", "bell peppers"], "prep_notes": "Pre-cut vegetables", "calories": 110, "protein": 5, "carbs": 10, "fat": 6, "fiber": 4}
            },
            "Wednesday": {
                "breakfast": {
                    "meal": "Chia pudding with tropical fruits",
                    "ingredients": ["chia seeds", "coconut milk", "mango", "pineapple", "honey"],
                    "prep_notes": "Prepare chia pudding the night before, let it set in refrigerator",
                    "calories": 320, "protein": 8, "carbs": 35, "fat": 16, "fiber": 12
                },
                "lunch": {
                    "meal": "Turkey and avocado wrap",
                    "ingredients": ["turkey slices", "avocado", "tortilla", "lettuce", "tomatoes", "mustard"],
                    "prep_notes": "Use fresh ingredients, prepare vegetables in advance",
                    "calories": 420, "protein": 25, "carbs": 35, "fat": 18, "fiber": 8
                },
                "dinner": {
                    "meal": "Lean beef stir-fry with vegetables",
                    "ingredients": ["lean beef", "mixed vegetables", "jasmine rice", "garlic", "soy sauce"],
                    "prep_notes": "Marinate beef for 2 hours, prep vegetables night before",
                    "calories": 510, "protein": 32, "carbs": 45, "fat": 16, "fiber": 6
                },
                "snack1": {"meal": "Protein energy balls", "ingredients": ["dates", "almonds", "protein powder", "coconut"], "prep_notes": "Make energy balls in advance and refrigerate", "calories": 140, "protein": 8, "carbs": 12, "fat": 7, "fiber": 3},
                "snack2": {"meal": "Cottage cheese with fruit", "ingredients": ["cottage cheese", "peaches", "cinnamon"], "prep_notes": "Use chilled cottage cheese", "calories": 130, "protein": 12, "carbs": 15, "fat": 2, "fiber": 2}
            },
            "Thursday": {
                "breakfast": {
                    "meal": "Avocado toast with poached egg",
                    "ingredients": ["whole grain bread", "avocado", "eggs", "tomatoes", "lime", "pepper"],
                    "prep_notes": "Use ripe avocado, prepare fresh",
                    "calories": 380, "protein": 16, "carbs": 30, "fat": 22, "fiber": 10
                },
                "lunch": {
                    "meal": "Lentil soup with crusty bread",
                    "ingredients": ["red lentils", "vegetables", "vegetable broth", "bread", "herbs"],
                    "prep_notes": "Soak lentils for 2 hours, chop vegetables night before",
                    "calories": 440, "protein": 20, "carbs": 65, "fat": 8, "fiber": 15
                },
                "dinner": {
                    "meal": "Grilled chicken with sweet potato",
                    "ingredients": ["chicken thighs", "sweet potato", "asparagus", "herbs", "olive oil"],
                    "prep_notes": "Marinate chicken overnight, pre-cut sweet potato",
                    "calories": 500, "protein": 35, "carbs": 40, "fat": 18, "fiber": 8
                },
                "snack1": {"meal": "Trail mix", "ingredients": ["nuts", "dried fruits", "dark chocolate"], "prep_notes": "Store in airtight container", "calories": 160, "protein": 5, "carbs": 15, "fat": 10, "fiber": 3},
                "snack2": {"meal": "Vegetable smoothie", "ingredients": ["cucumber", "celery", "apple", "lime"], "prep_notes": "Use fresh vegetables", "calories": 100, "protein": 2, "carbs": 20, "fat": 1, "fiber": 5}
            },
            "Friday": {
                "breakfast": {
                    "meal": "Protein pancakes with berries",
                    "ingredients": ["protein powder", "banana", "eggs", "oats", "berries"],
                    "prep_notes": "Prepare batter the night before, cook fresh",
                    "calories": 360, "protein": 25, "carbs": 35, "fat": 12, "fiber": 6
                },
                "lunch": {
                    "meal": "Asian-style poke bowl",
                    "ingredients": ["tuna", "sushi rice", "edamame", "cucumber", "sesame oil"],
                    "prep_notes": "Use sushi-grade fish, prepare rice in advance",
                    "calories": 460, "protein": 28, "carbs": 50, "fat": 14, "fiber": 5
                },
                "dinner": {
                    "meal": "Vegetable curry with basmati rice",
                    "ingredients": ["mixed vegetables", "coconut milk", "curry spices", "basmati rice"],
                    "prep_notes": "Soak basmati rice for 30 minutes, prep vegetables",
                    "calories": 470, "protein": 12, "carbs": 70, "fat": 16, "fiber": 10
                },
                "snack1": {"meal": "Banana with peanut butter", "ingredients": ["banana", "peanut butter"], "prep_notes": "Use natural peanut butter", "calories": 170, "protein": 6, "carbs": 20, "fat": 8, "fiber": 3},
                "snack2": {"meal": "Herbal tea with honey almonds", "ingredients": ["almonds", "honey", "herbal tea"], "prep_notes": "Lightly toast almonds", "calories": 110, "protein": 4, "carbs": 8, "fat": 8, "fiber": 2}
            },
            "Saturday": {
                "breakfast": {
                    "meal": "Weekend brunch omelet",
                    "ingredients": ["eggs", "cheese", "mushrooms", "spinach", "herbs"],
                    "prep_notes": "Use fresh herbs, room temperature eggs",
                    "calories": 390, "protein": 22, "carbs": 8, "fat": 28, "fiber": 3
                },
                "lunch": {
                    "meal": "Quinoa stuffed bell peppers",
                    "ingredients": ["bell peppers", "quinoa", "black beans", "corn", "cheese"],
                    "prep_notes": "Pre-cook quinoa, hollow out peppers night before",
                    "calories": 420, "protein": 18, "carbs": 55, "fat": 12, "fiber": 12
                },
                "dinner": {
                    "meal": "Pan-seared cod with roasted vegetables",
                    "ingredients": ["cod fillet", "zucchini", "bell peppers", "onions", "herbs"],
                    "prep_notes": "Bring fish to room temperature, prep vegetables",
                    "calories": 480, "protein": 30, "carbs": 25, "fat": 15, "fiber": 8
                },
                "snack1": {"meal": "Fruit salad with yogurt", "ingredients": ["mixed fruits", "yogurt", "mint"], "prep_notes": "Cut fruits fresh, chill", "calories": 140, "protein": 6, "carbs": 25, "fat": 3, "fiber": 4},
                "snack2": {"meal": "Dark chocolate with nuts", "ingredients": ["dark chocolate", "walnuts"], "prep_notes": "Use 70% cacao chocolate", "calories": 130, "protein": 3, "carbs": 10, "fat": 9, "fiber": 2}
            },
            "Sunday": {
                "breakfast": {
                    "meal": "Smoothie bowl with granola",
                    "ingredients": ["frozen fruits", "yogurt", "granola", "chia seeds", "honey"],
                    "prep_notes": "Freeze fruits overnight, use thick yogurt",
                    "calories": 370, "protein": 15, "carbs": 50, "fat": 12, "fiber": 8
                },
                "lunch": {
                    "meal": "Grilled vegetable and hummus sandwich",
                    "ingredients": ["whole grain bread", "zucchini", "eggplant", "hummus", "arugula"],
                    "prep_notes": "Grill vegetables in advance, store in refrigerator",
                    "calories": 400, "protein": 16, "carbs": 55, "fat": 14, "fiber": 10
                },
                "dinner": {
                    "meal": "Herb-crusted chicken with mashed cauliflower",
                    "ingredients": ["chicken breast", "cauliflower", "herbs", "garlic", "olive oil"],
                    "prep_notes": "Marinate chicken with herbs overnight, prep cauliflower",
                    "calories": 450, "protein": 35, "carbs": 20, "fat": 16, "fiber": 6
                },
                "snack1": {"meal": "Overnight oats parfait", "ingredients": ["oats", "yogurt", "berries", "nuts"], "prep_notes": "Layer ingredients night before", "calories": 180, "protein": 8, "carbs": 25, "fat": 6, "fiber": 5},
                "snack2": {"meal": "Herbal tea with dates", "ingredients": ["herbal tea", "dates", "almonds"], "prep_notes": "Stuff dates with almonds", "calories": 120, "protein": 3, "carbs": 18, "fat": 4, "fiber": 3}
            }
        }
        
        for day in days:
            fallback_plan[day] = daily_meals[day]
        
        # Customize based on diet type
        diet_type = user_profile.get('diet_type', 'Non-Vegetarian')
        if diet_type in ['Vegetarian', 'Vegan']:
            for day in days:
                fallback_plan[day]["lunch"]["meal"] = "Vegetarian protein bowl with legumes"
                fallback_plan[day]["lunch"]["ingredients"] = ["quinoa", "black beans", "chickpeas", "mixed vegetables", "tahini", "lemon"]
                fallback_plan[day]["dinner"]["meal"] = "Tofu stir-fry with brown rice and vegetables"
                fallback_plan[day]["dinner"]["ingredients"] = ["firm tofu", "brown rice", "broccoli", "bell peppers", "soy sauce", "ginger", "garlic"]
                if diet_type == 'Vegan':
                    fallback_plan[day]["snack1"]["meal"] = "Almond yogurt with berries"
                    fallback_plan[day]["snack1"]["ingredients"] = ["almond yogurt", "mixed berries", "maple syrup"]
                    fallback_plan[day]["breakfast"]["ingredients"] = ["rolled oats", "banana", "almonds", "blueberries", "oat milk", "maple syrup"]
        
        return {
            "generated_with_fallback": True,
            "original_error": error_msg,
            "raw_ai_response": raw_response[:500] + "..." if len(raw_response) > 500 else raw_response,
            **fallback_plan
        }
        
    except Exception as e:
        return {"error": f"Even fallback generation failed: {str(e)}", "raw_response": raw_response}

def generate_grocery_list(meal_plan):
    """Generate categorized grocery shopping list from meal plan"""
    if not meal_plan or "error" in meal_plan:
        return {}
    
    # Initialize grocery categories
    grocery_list = {
        "Proteins": set(),
        "Grains & Carbs": set(),
        "Vegetables": set(),
        "Fruits": set(),
        "Dairy & Alternatives": set(),
        "Pantry Items": set(),
        "Herbs & Spices": set(),
        "Others": set()
    }
    
    # Categorization mapping
    categories = {
        "Proteins": ["chicken", "fish", "beef", "pork", "turkey", "eggs", "tofu", "tempeh", "beans", "lentils", "chickpeas", "quinoa", "nuts", "almonds", "walnuts", "peanuts"],
        "Grains & Carbs": ["rice", "bread", "pasta", "oats", "quinoa", "barley", "wheat", "flour", "tortillas", "noodles"],
        "Vegetables": ["broccoli", "spinach", "kale", "tomatoes", "cucumber", "bell peppers", "onions", "garlic", "carrots", "celery", "mushrooms", "zucchini", "cauliflower", "lettuce", "greens"],
        "Fruits": ["banana", "apple", "berries", "blueberries", "strawberries", "oranges", "lemons", "avocado", "grapes", "mango", "pineapple"],
        "Dairy & Alternatives": ["milk", "yogurt", "cheese", "butter", "cream", "oat milk", "almond milk", "soy milk", "coconut milk", "almond yogurt"],
        "Herbs & Spices": ["herbs", "basil", "oregano", "thyme", "rosemary", "cilantro", "parsley", "ginger", "turmeric", "cumin", "paprika", "black pepper", "salt"],
        "Pantry Items": ["olive oil", "coconut oil", "vinegar", "soy sauce", "honey", "maple syrup", "tahini", "peanut butter", "vanilla", "baking soda", "flour"]
    }
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Extract ingredients from all meals
    for day in days:
        if day in meal_plan and isinstance(meal_plan[day], dict):
            for meal_type in ["breakfast", "lunch", "dinner", "snack1", "snack2"]:
                meal = meal_plan[day].get(meal_type, {})
                if isinstance(meal, dict) and "ingredients" in meal:
                    for ingredient in meal["ingredients"]:
                        ingredient_lower = ingredient.lower().strip()
                        
                        # Categorize ingredient
                        categorized = False
                        for category, keywords in categories.items():
                            if any(keyword in ingredient_lower for keyword in keywords):
                                grocery_list[category].add(ingredient.title())
                                categorized = True
                                break
                        
                        if not categorized:
                            grocery_list["Others"].add(ingredient.title())
    
    # Convert sets to sorted lists and add session state for checkboxes
    for category in grocery_list:
        grocery_list[category] = sorted(list(grocery_list[category]))
    
    return grocery_list

def generate_prep_reminders(meal_plan):
    """Generate intelligent meal prep reminders for each day"""
    if not meal_plan or "error" in meal_plan:
        return {}
    
    prep_reminders = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Define ingredients that commonly need advance preparation
    prep_ingredients = {
        "soak_overnight": ["oats", "chia seeds", "quinoa", "beans", "lentils", "rice", "almonds", "chickpeas"],
        "marinate": ["chicken", "fish", "beef", "pork", "turkey", "tofu", "paneer"],
        "defrost": ["frozen", "meat", "fish", "chicken", "seafood"],
        "chill": ["yogurt", "milk", "cream", "cheese"],
        "prep_vegetables": ["salad", "vegetables", "greens", "herbs"]
    }
    
    # Define cooking methods that need advance prep
    prep_methods = {
        "overnight": ["overnight oats", "chia pudding", "soaked", "fermented"],
        "marinated": ["marinated", "grilled", "bbq", "tandoori", "glazed"],
        "slow_cooked": ["slow cooked", "braised", "stewed", "crockpot"],
        "baked": ["baked", "roasted"] # Some baked items benefit from advance prep
    }
    
    for i, day in enumerate(days):
        if day in meal_plan and isinstance(meal_plan[day], dict):
            reminders = []
            
            for meal_type in ["breakfast", "lunch", "dinner", "snack1", "snack2"]:
                meal = meal_plan[day].get(meal_type, {})
                if isinstance(meal, dict):
                    meal_name = meal.get("meal", "Unknown meal")
                    ingredients = meal.get("ingredients", [])
                    prep_note = meal.get("prep_notes", "")
                    
                    detected_preps = []
                    
                    # Check explicit prep notes first
                    if prep_note and any(word in prep_note.lower() for word in ["soak", "marinate", "overnight", "freeze", "defrost", "advance", "chill", "prepare"]):
                        detected_preps.append(prep_note)
                    
                    # Intelligent detection based on ingredients
                    meal_lower = meal_name.lower()
                    
                    # Check for overnight preparation needs
                    if any(ing in meal_lower for ing in prep_ingredients["soak_overnight"]):
                        if "oats" in meal_lower or "overnight" in meal_lower:
                            detected_preps.append("Prepare overnight oats - mix ingredients and refrigerate")
                        elif any(grain in meal_lower for grain in ["quinoa", "rice", "beans", "lentils"]):
                            detected_preps.append("Soak grains/legumes overnight for better cooking")
                        elif "chia" in meal_lower:
                            detected_preps.append("Prepare chia pudding - mix and refrigerate overnight")
                    
                    # Check for marination needs
                    if any(protein in meal_lower for protein in prep_ingredients["marinate"]):
                        if any(method in meal_lower for method in ["grilled", "bbq", "tandoori", "marinated"]):
                            detected_preps.append(f"Marinate protein for {meal_name} (30 mins to 2 hours for best flavor)")
                    
                    # Check ingredients list for prep needs
                    for ingredient in ingredients:
                        ing_lower = ingredient.lower()
                        
                        # Frozen items need defrosting
                        if "frozen" in ing_lower:
                            detected_preps.append(f"Defrost {ingredient} overnight in refrigerator")
                        
                        # Some vegetables benefit from advance prep
                        if any(veg in ing_lower for veg in ["salad mix", "herbs", "greens"]) and meal_type in ["lunch", "dinner"]:
                            detected_preps.append("Wash and prep vegetables/herbs for easy cooking")
                    
                    # Check for specific meal types that need prep
                    if "salad" in meal_lower and meal_type in ["lunch", "dinner"]:
                        detected_preps.append("Wash and chop salad ingredients, store in refrigerator")
                    
                    if "smoothie" in meal_lower:
                        detected_preps.append("Pre-cut and freeze fruits for smoothie")
                    
                    if "soup" in meal_lower or "stew" in meal_lower:
                        detected_preps.append("Chop vegetables and prepare broth ingredients")
                    
                    # Add reminders if any prep needed
                    for prep in detected_preps:
                        reminders.append({
                            "meal": meal_name,
                            "meal_type": meal_type.replace("snack1", "Morning Snack").replace("snack2", "Evening Snack").title(),
                            "prep_note": prep,
                            "ingredients_used": ingredients[:3]  # Show first 3 ingredients for context
                        })
            
            if reminders:
                # Set reminder for previous day
                prev_day_index = (i - 1) % 7
                prev_day = days[prev_day_index]
                
                if prev_day not in prep_reminders:
                    prep_reminders[prev_day] = []
                
                prep_reminders[prev_day].extend([
                    {
                        "for_day": day,
                        "meal": reminder["meal"],
                        "meal_type": reminder["meal_type"],
                        "prep_note": reminder["prep_note"],
                        "ingredients_used": reminder["ingredients_used"]
                    } for reminder in reminders
                ])
    
    return prep_reminders

def format_user_profile_for_ai(profile):
    """Format user profile for AI context"""
    if not profile:
        return "No user profile available."
    
    profile_text = f"""
    - Gender: {profile.get('gender', 'Not specified')}
    - Age: {profile.get('age', 'Not specified')}
    - Weight: {profile.get('weight', 'Not specified')} kg
    - Height: {profile.get('height', 'Not specified')} cm
    - Diet Type: {profile.get('diet_type', 'Not specified')}
    - Activity Level: {profile.get('activity_level', 'Not specified')}
    - Health Goals: {profile.get('health_goals', 'Not specified')}
    - Food Allergies: {profile.get('allergies', 'None')}
    - Food Dislikes: {profile.get('dislikes', 'None')}
    - Food Preferences: {profile.get('likes', 'Not specified')}
    - Medical Conditions: {profile.get('medical_conditions', 'None')}
    """
    return profile_text.strip()

def user_profile_form():
    """Create user profile form"""
    st.header("👤 User Profile")
    
    with st.form("user_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
            age = st.number_input("Age", min_value=1, max_value=120, value=25)
            weight = st.number_input("Weight (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.1)
            height = st.number_input("Height (cm)", min_value=50, max_value=250, value=170)
            
        with col2:
            diet_type = st.selectbox("Diet Type", [
                "Vegetarian", "Non-Vegetarian", "Vegan", "Pescatarian", 
                "Keto", "Paleo", "Mediterranean", "Other"
            ])
            activity_level = st.selectbox("Activity Level", [
                "Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"
            ])
            health_goals = st.multiselect("Health Goals", [
                "Weight Loss", "Weight Gain", "Muscle Building", "Maintenance", 
                "Better Nutrition", "Improved Energy", "Heart Health", "Diabetes Management"
            ])
        
        allergies = st.text_area("Food Allergies (comma-separated)", 
                                placeholder="e.g., nuts, dairy, gluten, shellfish")
        dislikes = st.text_area("Food Dislikes (comma-separated)", 
                               placeholder="e.g., spicy food, mushrooms, fish")
        likes = st.text_area("Food Preferences/Likes (comma-separated)", 
                            placeholder="e.g., Italian cuisine, grilled foods, salads")
        medical_conditions = st.text_area("Medical Conditions (optional)", 
                                        placeholder="e.g., diabetes, hypertension, PCOS")
        
        submitted = st.form_submit_button("Save Profile & Generate Meal Plan")
        
        if submitted:
            profile = {
                "gender": gender,
                "age": age,
                "weight": weight,
                "height": height,
                "diet_type": diet_type,
                "activity_level": activity_level,
                "health_goals": health_goals,
                "allergies": allergies,
                "dislikes": dislikes,
                "likes": likes,
                "medical_conditions": medical_conditions
            }
            
            st.session_state.user_profile = profile
            st.session_state.profile_completed = True
            
            # Generate meal plan
            with st.spinner("Generating your personalized 7-day meal plan..."):
                meal_plan = generate_meal_plan(profile)
                st.session_state.meal_plan = meal_plan
                
                # Generate grocery list and prep reminders
                st.session_state.grocery_list = generate_grocery_list(meal_plan)
                st.session_state.prep_reminders = generate_prep_reminders(meal_plan)
                st.session_state.grocery_checked = {}  # Reset checkbox states
            
            st.success("✅ Profile saved, meal plan generated, and grocery list created!")
            st.rerun()

def display_meal_plan():
    """Display the 7-day meal plan"""
    if not st.session_state.meal_plan:
        st.info("👆 Please complete your profile to generate a meal plan.")
        return
    
    st.header("📅 Your 7-Day Meal Plan")
    
    # Check for fallback mode
    if st.session_state.meal_plan.get("generated_with_fallback"):
        st.warning("⚠️ Used fallback meal plan due to AI response formatting issues. Click 'Regenerate' for a new personalized plan.")
        with st.expander("🔍 Technical Details"):
            st.write(f"**Original Error:** {st.session_state.meal_plan.get('original_error', 'Unknown')}")
            if st.session_state.meal_plan.get('raw_ai_response'):
                st.text_area("Partial AI Response:", st.session_state.meal_plan['raw_ai_response'], height=100)
    
    if "error" in st.session_state.meal_plan and not st.session_state.meal_plan.get("generated_with_fallback"):
        st.error(f"Error generating meal plan: {st.session_state.meal_plan['error']}")
        if "raw_response" in st.session_state.meal_plan:
            st.text_area("Raw AI Response:", st.session_state.meal_plan['raw_response'], height=200)
        return
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Create tabs for each day
    day_tabs = st.tabs(days)
    
    for i, day in enumerate(days):
        with day_tabs[i]:
            if day in st.session_state.meal_plan:
                day_plan = st.session_state.meal_plan[day]
                
                def display_meal_with_nutrition(meal_data, meal_name, icon):
                    st.subheader(f"{icon} {meal_name}")
                    if isinstance(meal_data, dict) and "meal" in meal_data:
                        st.write(meal_data["meal"])
                        
                        # Show ingredients if available
                        if "ingredients" in meal_data and meal_data["ingredients"]:
                            with st.expander(f"🛒 Ingredients for {meal_name}"):
                                ingredients_text = ", ".join(meal_data["ingredients"])
                                st.write(ingredients_text)
                        
                        # Show prep notes if available
                        if "prep_notes" in meal_data and meal_data["prep_notes"]:
                            st.info(f"📝 **Prep Note:** {meal_data['prep_notes']}")
                        
                        # Display nutrition info in columns
                        ncol1, ncol2, ncol3, ncol4, ncol5 = st.columns(5)
                        with ncol1:
                            st.metric("Calories", f"{meal_data.get('calories', 'N/A')}")
                        with ncol2:
                            st.metric("Protein", f"{meal_data.get('protein', 'N/A')}g")
                        with ncol3:
                            st.metric("Carbs", f"{meal_data.get('carbs', 'N/A')}g")
                        with ncol4:
                            st.metric("Fat", f"{meal_data.get('fat', 'N/A')}g")
                        with ncol5:
                            st.metric("Fiber", f"{meal_data.get('fiber', 'N/A')}g")
                    else:
                        # Fallback for old format
                        st.write(meal_data if meal_data else "Not available")
                    st.divider()
                
                # Display meals for the day
                display_meal_with_nutrition(day_plan.get("breakfast"), "Breakfast", "🌅")
                display_meal_with_nutrition(day_plan.get("lunch"), "Lunch", "🍽️")
                display_meal_with_nutrition(day_plan.get("dinner"), "Dinner", "🌙")
                
                col1, col2 = st.columns(2)
                with col1:
                    display_meal_with_nutrition(day_plan.get("snack1"), "Snack 1", "🍎")
                with col2:
                    display_meal_with_nutrition(day_plan.get("snack2"), "Snack 2", "🥜")
                
                # Daily nutrition summary
                st.subheader("📊 Daily Nutrition Summary")
                total_calories = 0
                total_protein = 0
                total_carbs = 0
                total_fat = 0
                total_fiber = 0
                
                for meal_key in ["breakfast", "lunch", "dinner", "snack1", "snack2"]:
                    meal = day_plan.get(meal_key, {})
                    if isinstance(meal, dict):
                        total_calories += meal.get("calories", 0)
                        total_protein += meal.get("protein", 0)
                        total_carbs += meal.get("carbs", 0)
                        total_fat += meal.get("fat", 0)
                        total_fiber += meal.get("fiber", 0)
                
                summary_col1, summary_col2, summary_col3, summary_col4, summary_col5 = st.columns(5)
                with summary_col1:
                    st.metric("Total Calories", f"{total_calories}")
                with summary_col2:
                    st.metric("Total Protein", f"{total_protein}g")
                with summary_col3:
                    st.metric("Total Carbs", f"{total_carbs}g")
                with summary_col4:
                    st.metric("Total Fat", f"{total_fat}g")
                with summary_col5:
                    st.metric("Total Fiber", f"{total_fiber}g")
            else:
                st.error(f"No meal plan available for {day}")
    
    # Weekly nutrition summary
    st.header("📈 Weekly Nutrition Summary")
    
    if st.session_state.meal_plan and "error" not in st.session_state.meal_plan:
        weekly_calories = 0
        weekly_protein = 0
        weekly_carbs = 0
        weekly_fat = 0
        weekly_fiber = 0
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day in days:
            if day in st.session_state.meal_plan:
                day_plan = st.session_state.meal_plan[day]
                for meal_key in ["breakfast", "lunch", "dinner", "snack1", "snack2"]:
                    meal = day_plan.get(meal_key, {})
                    if isinstance(meal, dict):
                        weekly_calories += meal.get("calories", 0)
                        weekly_protein += meal.get("protein", 0)
                        weekly_carbs += meal.get("carbs", 0)
                        weekly_fat += meal.get("fat", 0)
                        weekly_fiber += meal.get("fiber", 0)
        
        wcol1, wcol2, wcol3, wcol4, wcol5 = st.columns(5)
        with wcol1:
            st.metric("Weekly Calories", f"{weekly_calories:,}")
            st.metric("Daily Avg", f"{weekly_calories//7:,}")
        with wcol2:
            st.metric("Weekly Protein", f"{weekly_protein}g")
            st.metric("Daily Avg", f"{weekly_protein//7}g")
        with wcol3:
            st.metric("Weekly Carbs", f"{weekly_carbs}g")
            st.metric("Daily Avg", f"{weekly_carbs//7}g")
        with wcol4:
            st.metric("Weekly Fat", f"{weekly_fat}g")
            st.metric("Daily Avg", f"{weekly_fat//7}g")
        with wcol5:
            st.metric("Weekly Fiber", f"{weekly_fiber}g")
            st.metric("Daily Avg", f"{weekly_fiber//7}g")
    
    st.divider()
    
    # Regenerate meal plan button
    if st.button("🔄 Regenerate Meal Plan"):
        with st.spinner("Generating new meal plan..."):
            meal_plan = generate_meal_plan(st.session_state.user_profile)
            st.session_state.meal_plan = meal_plan
            
            # Regenerate grocery list and prep reminders
            st.session_state.grocery_list = generate_grocery_list(meal_plan)
            st.session_state.prep_reminders = generate_prep_reminders(meal_plan)
            st.session_state.grocery_checked = {}  # Reset checkbox states
        st.rerun()

def chat_sidebar():
    """Chat functionality in sidebar"""
    with st.sidebar:
        st.header("💬 Chat with AI")
        st.markdown("Ask any cooking or nutrition questions!")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Chat input
        user_input = st.text_input("Ask a question...", key="chat_input")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Send", key="send_chat"):
                if user_input:
                    # Add user message
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    
                    # Get AI response with user context
                    user_context = format_user_profile_for_ai(st.session_state.user_profile)
                    response = get_openai_response(st.session_state.messages, user_context)
                    
                    # Add AI response
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    st.rerun()
        
        with col2:
            if st.button("Clear", key="clear_chat"):
                st.session_state.chat_history = []
                st.session_state.messages = []
                st.rerun()

def display_grocery_list():
    """Display interactive grocery shopping list"""
    st.header("🛒 Grocery Shopping List")
    
    if not st.session_state.grocery_list:
        st.info("👆 Generate a meal plan first to create your grocery list.")
        return
    
    total_items = sum(len(items) for items in st.session_state.grocery_list.values() if items)
    checked_items = sum(1 for items in st.session_state.grocery_checked.values() for checked in items.values() if checked)
    
    progress = checked_items / total_items if total_items > 0 else 0
    st.progress(progress, text=f"Shopping Progress: {checked_items}/{total_items} items ({progress:.0%})")
    
    # Shopping list by categories
    for category, items in st.session_state.grocery_list.items():
        if items:  # Only show categories with items
            st.subheader(f"📂 {category}")
            
            # Initialize category in checked items if not exists
            if category not in st.session_state.grocery_checked:
                st.session_state.grocery_checked[category] = {}
            
            for item in items:
                # Initialize item if not exists
                if item not in st.session_state.grocery_checked[category]:
                    st.session_state.grocery_checked[category][item] = False
                
                # Create checkbox
                checked = st.checkbox(
                    item,
                    value=st.session_state.grocery_checked[category][item],
                    key=f"grocery_{category}_{item}"
                )
                st.session_state.grocery_checked[category][item] = checked
            
            st.divider()
    
    # Clear all checkboxes button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Check All Items"):
            for category in st.session_state.grocery_checked:
                for item in st.session_state.grocery_checked[category]:
                    st.session_state.grocery_checked[category][item] = True
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset All Items"):
            for category in st.session_state.grocery_checked:
                for item in st.session_state.grocery_checked[category]:
                    st.session_state.grocery_checked[category][item] = False
            st.rerun()

def display_prep_reminders():
    """Display intelligent meal prep reminders for each day"""
    st.header("⏰ Smart Meal Prep Reminders")
    
    if not st.session_state.prep_reminders:
        st.info("👆 Generate a meal plan first to see intelligent prep reminders.")
        return
    
    st.markdown("**🎯 Plan ahead for stress-free cooking! Here's your personalized prep schedule:**")
    
    # Show today's reminders prominently if available
    from datetime import datetime
    today = datetime.now().strftime("%A")
    
    if today in st.session_state.prep_reminders:
        st.warning(f"⚡ **TODAY'S PREP TASKS ({today} Evening)**")
        reminders = st.session_state.prep_reminders[today]
        for i, reminder in enumerate(reminders, 1):
            st.info(f"""
            **Task {i}: Prep for Tomorrow's {reminder['meal_type']}**  
            🍽️ **Meal:** {reminder['meal']}  
            📝 **Action:** {reminder['prep_note']}  
            🛒 **Key Ingredients:** {', '.join(reminder.get('ingredients_used', []))}
            """)
        st.success(f"✅ Complete these {len(reminders)} task(s) tonight for an easier tomorrow!")
        st.divider()
    
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    
    # Create tabs for each day
    prep_tabs = st.tabs(days)
    
    for i, day in enumerate(days):
        with prep_tabs[i]:
            st.subheader(f"📅 {day} Evening Prep Tasks")
            
            if day in st.session_state.prep_reminders:
                reminders = st.session_state.prep_reminders[day]
                
                # Group reminders by the day they're for
                for j, reminder in enumerate(reminders, 1):
                    with st.expander(f"Task {j}: {reminder['meal_type']} - {reminder['meal']}", expanded=(day == today)):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**🍽️ Meal:** {reminder['meal']}")
                            st.write(f"**📅 For:** {reminder['for_day']}'s {reminder['meal_type']}")
                            st.write(f"**📝 Prep Task:** {reminder['prep_note']}")
                        
                        with col2:
                            if reminder.get('ingredients_used'):
                                st.write("**🛒 Key Ingredients:**")
                                for ingredient in reminder['ingredients_used']:
                                    st.write(f"• {ingredient}")
                        
                        # Add completion checkbox
                        checkbox_key = f"prep_complete_{day}_{j}"
                        completed = st.checkbox(
                            "✅ Mark as completed",
                            key=checkbox_key,
                            help="Check this when you've completed the prep task"
                        )
                        
                        if completed:
                            st.success("Great job! This prep task is done.")
                
                # Summary for the day
                total_tasks = len(reminders)
                next_day = days[(i + 1) % 7]
                st.markdown(f"**📊 Summary:** {total_tasks} prep task(s) for an easier {next_day}")
                
                # Time estimate
                st.info(f"⏱️ **Estimated prep time:** {total_tasks * 5}-{total_tasks * 15} minutes")
                
            else:
                st.write("🎉 No advance prep needed for tomorrow's meals!")
                st.write("You can relax tonight! 😊")
                if day == "Sunday":
                    st.balloons()  # Fun touch for Sunday

def display_user_summary():
    """Display user profile summary"""
    if st.session_state.user_profile:
        with st.expander("👤 View Profile Summary"):
            profile = st.session_state.user_profile
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Age", f"{profile.get('age', 'N/A')} years")
                st.metric("Weight", f"{profile.get('weight', 'N/A')} kg")
            with col2:
                st.metric("Height", f"{profile.get('height', 'N/A')} cm")
                if profile.get('weight') and profile.get('height'):
                    bmi = profile['weight'] / ((profile['height']/100) ** 2)
                    st.metric("BMI", f"{bmi:.1f}")
            with col3:
                st.write(f"**Diet:** {profile.get('diet_type', 'N/A')}")
                st.write(f"**Activity:** {profile.get('activity_level', 'N/A')}")
            
            if profile.get('health_goals'):
                st.write(f"**Goals:** {', '.join(profile['health_goals'])}")

def main():
    # Page configuration
    st.set_page_config(
        page_title="Meal Planner AI",
        page_icon="🍽️",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # App title
    st.title("🍽️ Personalized Meal Planner AI")
    st.markdown("Get personalized meal plans and cooking advice based on your profile!")
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ OpenAI API key not found! Please check your .env file.")
        return
    
    # Chat sidebar
    chat_sidebar()
    
    # Main content area
    if not st.session_state.profile_completed:
        user_profile_form()
    else:
        # Display profile summary
        display_user_summary()
        
        # Quick prep reminder dashboard
        if st.session_state.prep_reminders:
            from datetime import datetime
            today = datetime.now().strftime("%A")
            
            if today in st.session_state.prep_reminders:
                st.warning(f"⚡ **Today's Prep Reminders ({today} Evening)**")
                reminders = st.session_state.prep_reminders[today]
                
                cols = st.columns(min(len(reminders), 3))
                for i, reminder in enumerate(reminders[:3]):  # Show max 3 in dashboard
                    with cols[i]:
                        st.info(f"""
                        **{reminder['meal_type']}**  
                        {reminder['meal'][:30]}{'...' if len(reminder['meal']) > 30 else ''}  
                        📝 {reminder['prep_note'][:40]}{'...' if len(reminder['prep_note']) > 40 else ''}
                        """)
                
                if len(reminders) > 3:
                    st.caption(f"+ {len(reminders) - 3} more prep tasks. Check the Prep Reminders tab for details.")
                
                st.divider()
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Meal Plan", "🛒 Grocery List", "⏰ Prep Reminders", "👤 Edit Profile", "📊 Nutrition Tips"])
        
        with tab1:
            display_meal_plan()
        
        with tab2:
            display_grocery_list()
        
        with tab3:
            display_prep_reminders()
        
        with tab4:
            st.info("Update your profile to regenerate meal plan")
            user_profile_form()
        
        with tab5:
            st.header("📊 Nutrition Tips")
            if st.session_state.user_profile:
                profile = st.session_state.user_profile
                
                # Calculate and display nutrition info
                if profile.get('weight') and profile.get('height') and profile.get('age'):
                    # Basic BMR calculation (Mifflin-St Jeor Equation)
                    if profile.get('gender') == 'Male':
                        bmr = 10 * profile['weight'] + 6.25 * profile['height'] - 5 * profile['age'] + 5
                    else:
                        bmr = 10 * profile['weight'] + 6.25 * profile['height'] - 5 * profile['age'] - 161
                    
                    activity_multipliers = {
                        "Sedentary": 1.2,
                        "Lightly Active": 1.375,
                        "Moderately Active": 1.55,
                        "Very Active": 1.725,
                        "Extremely Active": 1.9
                    }
                    
                    multiplier = activity_multipliers.get(profile.get('activity_level', 'Moderately Active'), 1.55)
                    daily_calories = bmr * multiplier
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Daily Calories", f"{daily_calories:.0f}")
                    with col2:
                        recommended_protein = profile['weight'] * 1.2
                        if 'Muscle Building' in profile.get('health_goals', []):
                            recommended_protein = profile['weight'] * 1.8
                        st.metric("Protein (g)", f"{recommended_protein:.0f}")
                    with col3:
                        # Carbs: 45-65% of total calories
                        carb_calories = daily_calories * 0.50  # Using 50% as middle ground
                        carb_grams = carb_calories / 4  # 4 calories per gram of carbs
                        st.metric("Carbs (g)", f"{carb_grams:.0f}")
                        # Fat: 20-35% of total calories
                        fat_calories = daily_calories * 0.25  # Using 25% as middle ground
                        fat_grams = fat_calories / 9  # 9 calories per gram of fat
                        st.metric("Fat (g)", f"{fat_grams:.0f}")
                    with col5:
                        st.metric("Water (L)", f"{profile['weight'] * 0.035:.1f}")
                
                # Health tips based on profile
                st.subheader("💡 Personalized Tips")
                
                tips = []
                if 'Weight Loss' in profile.get('health_goals', []):
                    tips.append("🔥 Focus on creating a moderate caloric deficit through balanced nutrition and exercise")
                if 'Muscle Building' in profile.get('health_goals', []):
                    tips.append("💪 Ensure adequate protein intake (1.6-2.2g per kg body weight)")
                if profile.get('diet_type') == 'Vegetarian':
                    tips.append("🌱 Include complementary proteins like rice & beans for complete amino acid profiles")
                if profile.get('allergies'):
                    tips.append("⚠️ Always check ingredient labels and inform restaurants about your allergies")
                
                for tip in tips:
                    st.info(tip)

if __name__ == "__main__":
    main() 