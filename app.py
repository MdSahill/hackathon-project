import streamlit as st
import json
import os
import tempfile
from datetime import datetime
from utils.storage import DataStorage
from utils.voice_processing import VoiceProcessor
from utils.matching import MatchMaker
from dotenv import load_dotenv

load_dotenv()

# Initialize services
# Change 'json' to 'csv' or 'gsheets' as needed
storage = DataStorage(storage_type='json')
voice_processor = VoiceProcessor()
match_maker = MatchMaker()

def main():
    st.title("AI-Powered Dating Matchmaker")
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'profile_data' not in st.session_state:
        st.session_state.profile_data = None
    
    # App navigation
    if not st.session_state.user_id:
        show_auth_section()
    else:
        show_main_app()

def show_auth_section():
    st.header("Create Your Profile")
    
    with st.form("profile_form"):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=18, max_value=100)
        gender = st.selectbox("Gender", ["Male", "Female", "Non-binary", "Other"])
        bio = st.text_area("Tell us about yourself", 
                         help="Describe your personality, interests, and what you're looking for in a partner")
        
        # Voice input option
        st.write("Or record your bio:")
        audio_file = st.file_uploader("Upload audio recording", type=["wav", "mp3"])
        
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            if audio_file:
                # Save audio to temp file and transcribe
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_file.read())
                    bio = voice_processor.transcribe_audio(tmp.name)
                    os.unlink(tmp.name)
                
                if not bio:
                    st.error("Failed to transcribe audio. Please try again or type your bio.")
                    return
            
            if not bio:
                st.error("Please provide a bio either by text or audio")
                return
            
            # Analyze profile with AI
            profile_analysis = match_maker.analyze_profile(bio)
            try:
                profile_analysis = json.loads(profile_analysis)
            except json.JSONDecodeError:
                st.error("Failed to analyze profile. Please try again.")
                return
            
            # Create user in storage
            user_data = {
                "name": name,
                "age": age,
                "gender": gender,
                "bio": bio,
                "personality_traits": profile_analysis.get("personality_traits", []),
                "interests": profile_analysis.get("interests", []),
                "values": profile_analysis.get("values", []),
                "looking_for": profile_analysis.get("looking_for", "")
            }
            
            user = storage.create_user(user_data)
            if user:
                st.session_state.user_id = user['id']
                st.session_state.profile_data = user
                st.rerun()
            else:
                st.error("Failed to create profile. Please try again.")

def show_main_app():
    st.sidebar.header("Your Profile")
    st.sidebar.write(f"**Name:** {st.session_state.profile_data['name']}")
    st.sidebar.write(f"**Age:** {st.session_state.profile_data['age']}")
    st.sidebar.write("**About You:**")
    st.sidebar.write(st.session_state.profile_data['bio'])
    
    if st.sidebar.button("Find New Matches"):
        st.session_state.matches = None
    
    st.header("Your Matches")
    
    if 'matches' not in st.session_state or not st.session_state.matches:
        all_users = storage.get_all_users()
        potential_matches = [
            user for user in all_users 
            if user['id'] != st.session_state.user_id
        ]
        
        matches_with_compatibility = []
        
        for match in potential_matches[:5]:  # Limit to 5 matches for demo
            compatibility = match_maker.calculate_compatibility(
                json.dumps(st.session_state.profile_data),
                json.dumps(match)
            )
            try:
                compatibility_data = json.loads(compatibility)
                matches_with_compatibility.append({
                    "user": match,
                    "compatibility": compatibility_data
                })
            except json.JSONDecodeError:
                continue
        
        # Sort by compatibility score
        matches_with_compatibility.sort(
            key=lambda x: x["compatibility"].get("compatibility_score", 0), 
            reverse=True
        )
        st.session_state.matches = matches_with_compatibility
    
    if not st.session_state.matches:
        st.write("No matches found. Try updating your profile to attract more matches.")
        return
    
    for idx, match in enumerate(st.session_state.matches):
        with st.expander(f"Match {idx+1}: {match['user']['name']}, {match['user']['age']}"):
            st.write(f"**Compatibility Score:** {match['compatibility'].get('compatibility_score', 'N/A')}/100")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Strengths")
                st.write(match['compatibility'].get('strengths', 'No data available'))
                
            with col2:
                st.subheader("Potential Challenges")
                st.write(match['compatibility'].get('potential_challenges', 'No data available'))
            
            st.subheader("About Them")
            st.write(match['user']['bio'])
            
            st.subheader("Conversation Starters")
            for starter in match['compatibility'].get('conversation_starters', []):
                st.write(f"- {starter}")
            
            if st.button(f"Message {match['user']['name']}", key=f"message_{idx}"):
                st.session_state.current_chat = match['user']['id']
                st.rerun()

if __name__ == "__main__":
    main()