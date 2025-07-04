import os
from openrouter import OpenRouter
from dotenv import load_dotenv

load_dotenv()

class MatchMaker:
    def __init__(self):
        self.client = OpenRouter(api_key=os.environ.get("OPENROUTER_API_KEY"))
    
    def analyze_profile(self, profile_text: str):
        prompt = f"""
        Analyze the following dating profile and extract key personality traits, interests, 
        and preferences. Return the analysis in JSON format with these fields:
        - personality_traits (list of 5 key traits)
        - interests (list of 5 main interests)
        - values (list of 3 core values)
        - looking_for (description of what they're looking for in a partner)
        
        Profile:
        {profile_text}
        """
        
        response = self.client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    def calculate_compatibility(self, profile1: dict, profile2: dict):
        prompt = f"""
        Calculate compatibility between two dating profiles based on their traits, 
        interests, and values. Return a JSON response with:
        - compatibility_score (0-100)
        - strengths (what makes them compatible)
        - potential_challenges
        - conversation_starters (list of 3 personalized icebreakers)
        
        Profile 1:
        {profile1}
        
        Profile 2:
        {profile2}
        """
        
        response = self.client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content