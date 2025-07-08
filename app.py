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

CRITICAL: Respond with ONLY valid JSON. No extra text, no markdown, no explanations.

JSON format:
{{
  "Monday": {{
    "breakfast": {{"meal": "description", "calories": 350, "protein": 15, "carbs": 45, "fat": 12, "fiber": 6}},
    "lunch": {{"meal": "description", "calories": 450, "protein": 25, "carbs": 55, "fat": 15, "fiber": 8}},
    "dinner": {{"meal": "description", "calories": 500, "protein": 30, "carbs": 50, "fat": 18, "fiber": 10}},
    "snack1": {{"meal": "description", "calories": 150, "protein": 8, "carbs": 15, "fat": 6, "fiber": 3}},
    "snack2": {{"meal": "description", "calories": 120, "protein": 5, "carbs": 12, "fat": 4, "fiber": 2}}
  }},
  "Tuesday": {{...same structure...}},
  "Wednesday": {{...same structure...}},
  "Thursday": {{...same structure...}},
  "Friday": {{...same structure...}},
  "Saturday": {{...same structure...}},
  "Sunday": {{...same structure...}}
}}

Respect dietary restrictions and preferences. Use realistic nutrition values."""
        
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
        # Create a basic meal plan structure
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        fallback_plan = {}
        
        for day in days:
            fallback_plan[day] = {
                "breakfast": {
                    "meal": "Oatmeal with fruits and nuts",
                    "calories": 350,
                    "protein": 12,
                    "carbs": 45,
                    "fat": 10,
                    "fiber": 8
                },
                "lunch": {
                    "meal": "Grilled chicken salad with vegetables",
                    "calories": 450,
                    "protein": 30,
                    "carbs": 25,
                    "fat": 15,
                    "fiber": 6
                },
                "dinner": {
                    "meal": "Baked fish with quinoa and vegetables",
                    "calories": 500,
                    "protein": 35,
                    "carbs": 40,
                    "fat": 18,
                    "fiber": 7
                },
                "snack1": {
                    "meal": "Greek yogurt with berries",
                    "calories": 150,
                    "protein": 10,
                    "carbs": 15,
                    "fat": 5,
                    "fiber": 3
                },
                "snack2": {
                    "meal": "Mixed nuts and dried fruits",
                    "calories": 120,
                    "protein": 4,
                    "carbs": 12,
                    "fat": 8,
                    "fiber": 2
                }
            }
        
        # Customize based on diet type
        diet_type = user_profile.get('diet_type', 'Non-Vegetarian')
        if diet_type in ['Vegetarian', 'Vegan']:
            for day in days:
                fallback_plan[day]["lunch"]["meal"] = "Vegetarian protein bowl with legumes"
                fallback_plan[day]["dinner"]["meal"] = "Tofu stir-fry with brown rice and vegetables"
                if diet_type == 'Vegan':
                    fallback_plan[day]["snack1"]["meal"] = "Almond yogurt with berries"
        
        return {
            "generated_with_fallback": True,
            "original_error": error_msg,
            "raw_ai_response": raw_response[:500] + "..." if len(raw_response) > 500 else raw_response,
            **fallback_plan
        }
        
    except Exception as e:
        return {"error": f"Even fallback generation failed: {str(e)}", "raw_response": raw_response}

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
            
            st.success("✅ Profile saved and meal plan generated!")
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
        
        # Main tabs
        tab1, tab2, tab3 = st.tabs(["📅 Meal Plan", "👤 Edit Profile", "📊 Nutrition Tips"])
        
        with tab1:
            display_meal_plan()
        
        with tab2:
            st.info("Update your profile to regenerate meal plan")
            user_profile_form()
        
        with tab3:
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