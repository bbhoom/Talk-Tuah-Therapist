import streamlit as st
import speech_recognition as sr
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
from gtts import gTTS
from streamlit_drawable_canvas import st_canvas
from datetime import datetime  # Importing datetime class
import random
import time
import requests
import streamlit as st
import numpy as np
from scipy.io import wavfile
import io
import time
from pathlib import Path



# Constants
PAT = 'aca1f67c23dd450b8b9306882d849a76'
USER_ID = 'anthropic'
APP_ID = 'completion'
MODEL_ID = 'claude-3-opus'
MODEL_VERSION_ID = '0b59b93d35864b9b88699a557629babf'



def init_styles():
    # Set page config FIRST, before any other Streamlit commands
    st.set_page_config(
        page_title="Talk Tuah Therapist",
        page_icon="🧠",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Page background style
    page_bg_style = """
    <style>
     .stButton button {
        background-color: #236860;
        color: white;
        padding: 15px 30px;
        border-radius: 25px;
        width: 100%;
    }
    .stTab {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    .css-1d391kg {
        padding: 1rem;
    }
    </style>
    """
    
    # Apply markdown styles
    st.markdown(page_bg_style, unsafe_allow_html=True)


def generate_response(user_message):
    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)
    metadata = (('authorization', 'Key ' + PAT),)
    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

    try:
        response = stub.PostModelOutputs(
            service_pb2.PostModelOutputsRequest(
                user_app_id=userDataObject,
                model_id=MODEL_ID,
                version_id=MODEL_VERSION_ID,
                inputs=[resources_pb2.Input(data=resources_pb2.Data(
                    text=resources_pb2.Text(raw=user_message)))]
            ),
            metadata=metadata
        )

        if response.status.code != status_code_pb2.SUCCESS:
            raise Exception(f"API call failed: {response.status.description}")

        return response.outputs[0].data.text.raw
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return None


def record_and_transcribe():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            with st.spinner("Adjusting for ambient noise..."):
                recognizer.adjust_for_ambient_noise(source)

            st.info("🎤 Listening... Please speak now.")
            audio_data = recognizer.listen(source, timeout=5)

            with st.spinner("Transcribing..."):
                try:
                    transcription = recognizer.recognize_google(audio_data)
                    return transcription
                except sr.UnknownValueError:
                    st.error("Could not understand the audio. Please try again.")
                except sr.RequestError:
                    st.error("Could not connect to speech recognition service.")
    except Exception as e:
        st.error(f"Error accessing microphone: {e}")
    return None


def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        audio_file = "response.mp3"
        tts.save(audio_file)
        return audio_file
    except Exception as e:
        st.error(f"Error generating audio: {e}")
        return None


def chatbot_page():
    st.header("💭 Chat with Me")
    
    # Initialize messages in session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Input methods
    st.write("### Choose Input Method")
    input_method = st.radio("", ["Text Input", "Voice Recording"])
    
    if input_method == "Text Input":
        # Text input option
        user_text = st.text_input("Type your message:", key="text_input")
        if st.button("Send"):
            if user_text:
                process_message(user_text)
    
    else:
        # Voice recording option
        if st.button("🎤 Start Recording"):
            transcription = record_and_transcribe()
            if transcription:
                st.success(f"You said: {transcription}")
                process_message(transcription)
    
    # Display chat history
    st.write("### Chat History")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

def process_message(message_text):
    response = generate_response(message_text)
    if response:
        st.session_state.messages.append({"role": "user", "content": message_text})
        st.session_state.messages.append({"role": "assistant", "content": response})
        audio_file = speak(response)
        if audio_file:
            st.audio(audio_file)



def game_center_page():
    tab1, tab2 = st.tabs(["Memory Matcher", "Rock Paper Scissors"])

    with tab1:
        st.title("🧠 Memory Matcher")
        
        # Game setup
        if 'game_state' not in st.session_state:
            # Generate 12 unique emoji pairs
            emojis = ['🍎', '🍌', '🍇', '🍊', '🍉', '🍓', 
                      '🚗', '🚀', '🎈', '🏀', '🐶', '🐱']
            board = emojis * 2  # Create pairs
            random.shuffle(board)  # Shuffle the board
            
            st.session_state.game_state = {
                'board': board,
                'flipped': [],
                'matched': [],
                'attempts': 0,
                'game_over': False
            }
        
        game = st.session_state.game_state
        
        # Game grid with 12 buttons
        cols = st.columns(4)  # Create 4 columns for layout
        for i in range(12):  # Loop through all 12 cards
            with cols[i % 4]:  # Distribute cards across columns
                if i not in game['matched']:
                    if i in game['flipped']:
                        # Show the emoji if the card is flipped
                        st.button(game['board'][i], disabled=True, key=f"flipped_{i}")
                    else:
                        # Show a button to flip the card
                        if st.button(f"Card {i+1}", key=f"card_{i}"):
                            game['flipped'].append(i)
                            
                            # Match logic
                            if len(game['flipped']) == 2:
                                game['attempts'] += 1
                                first, second = game['flipped']
                                if game['board'][first] == game['board'][second]:
                                    game['matched'].extend(game['flipped'])
                                else:
                                    # Reset flipped after a short delay if no match
                                    time.sleep(1)
                                
                                # Clear flipped cards after processing
                                game['flipped'] = []
                else:
                    # Show the matched emoji
                    st.button(game['board'][i], disabled=True, key=f"matched_{i}")
        
        # Game status
        st.write(f"Attempts: {game['attempts']}")
        
        # Win condition
        if len(game['matched']) == 12:  # All pairs found (12 emojis)
            st.balloons()
            st.success("Congratulations! You found all pairs! 🎉")
            game['game_over'] = True
        
        # Reset game button (only visible if the game is over)
        if game.get('game_over'):
            if st.button("New Game", key="new_game"):
                del st.session_state.game_state

    with tab2:
        st.title("✊ Rock Paper Scissors Showdown!")

        # Custom styling for hand animations (optional)
        st.markdown("""
        <style>
        .hand-container {
            display: flex;
            justify-content: space-between;
            font-size: 100px;
            margin: 20px 0;
            transition: transform 0.3s ease;
        }
        .hand-move {
            animation: shake 0.5s;
        }
        @keyframes shake {
            0% { transform: rotate(0deg); }
            25% { transform: rotate(15deg); }
            50% { transform: rotate(-15deg); }
            75% { transform: rotate(15deg); }
            100% { transform: rotate(0deg); }
        }
        </style>
        """, unsafe_allow_html=True)

        # Game choices with emojis
        choices = ['Rock ✊', 'Paper ✋', 'Scissors ✌️']

        # Player's choice
        player_choice = st.radio("Make your choice", choices)

        if st.button("Play"):
            # Computer's random choice
            computer_choice = random.choice(choices)

            # Animated loading
            with st.spinner('Battling it out...'):
                time.sleep(1)  # Dramatic pause

            # Create two columns for choice reveal
            col1, col2 = st.columns(2)

            with col1:
                st.write("### Your Choice")
                st.markdown(f"## {player_choice}")

            with col2:
                st.write("### Computer's Choice")
                st.markdown(f"## {computer_choice}")

            # Determine winner and show result with animations
            if player_choice == computer_choice:
                st.balloons()
                st.info("### It's a tie! 🤝")
            elif (
                (player_choice == 'Rock ✊' and computer_choice == 'Scissors ✌️') or
                (player_choice == 'Paper ✋' and computer_choice == 'Rock ✊') or
                (player_choice == 'Scissors ✌️' and computer_choice == 'Paper ✋')
            ):
                st.snow()
                st.success("### You win! 🎉🏆")
            else:
                st.error("### Computer wins! That's always OK, TRY AGAIN! 😢🤖")

def breathing_center_page():
    st.header("🫁 Breathing Center")

    # Custom CSS for animations
    st.markdown("""
        <style>
        @keyframes breathe {
            0% { transform: scale(1); opacity: 0.3; }
            50% { transform: scale(1.5); opacity: 0.8; }
            100% { transform: scale(1); opacity: 0.3; }
        }
        .breathing-circle {
            width: 100px;
            height: 100px;
            background: radial-gradient(circle, #236860, #2E7D32);
            border-radius: 50%;
            margin: 20px auto;
            animation: breathe 8s infinite ease-in-out;
            
        }
        .exercise-card {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color:black;
        }
        .timer-text {
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            color: #2E7D32;
        }
        </style>
    """, unsafe_allow_html=True)

    # Display breathing animation
    st.markdown('<div class="breathing-circle"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        breathing_exercise = st.selectbox(
            "Select a breathing exercise:",
            ["Box Breathing", "4-7-8 Breathing", "Deep Breathing"]
        )

    # Exercise descriptions
    descriptions = {
        "Box Breathing": "Box breathing is a powerful stress-relief technique used by Navy SEALs.",
        "4-7-8 Breathing": "This technique helps reduce anxiety and aids better sleep.",
        "Deep Breathing": "Simple yet effective way to reduce stress and increase mindfulness."
    }

    st.markdown(
        f'<div class="exercise-card">{descriptions[breathing_exercise]}</div>', unsafe_allow_html=True)

    if st.button("Start Exercise", key="start_breathing"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        if breathing_exercise == "Box Breathing":
            for cycle in range(4):
                for phase, duration in [("Inhale", 4), ("Hold", 4), ("Exhale", 4), ("Hold", 4)]:
                    status_text.markdown(
                        f'<p class="timer-text">{phase}</p>', unsafe_allow_html=True)
                    for i in range(duration):
                        progress_bar.progress((i + 1) / duration)
                        time.sleep(1)
                    progress_bar.progress(0)

        elif breathing_exercise == "4-7-8 Breathing":
            for cycle in range(4):
                for phase, duration in [("Inhale", 4), ("Hold", 7), ("Exhale", 8)]:
                    status_text.markdown(
                        f'<p class="timer-text">{phase}</p>', unsafe_allow_html=True)
                    for i in range(duration):
                        progress_bar.progress((i + 1) / duration)
                        time.sleep(1)
                    progress_bar.progress(0)

        elif breathing_exercise == "Deep Breathing":
            for cycle in range(4):
                for phase, duration in [("Inhale Deeply", 4), ("Hold", 2), ("Exhale Slowly", 4), ("Rest", 2)]:
                    status_text.markdown(
                        f'<p class="timer-text">{phase}</p>', unsafe_allow_html=True)
                    for i in range(duration):
                        progress_bar.progress((i + 1) / duration)
                        time.sleep(1)
                    progress_bar.progress(0)

        st.success("Exercise completed! Take a moment to notice how you feel.")



def journal_page():
    st.title("📝 Personal Journal")
    
    # Initialize the journal entries list in session state if not already done
    if 'journal_entries' not in st.session_state:
        st.session_state.journal_entries = []
    
    # Create a main container for better layout
    with st.container():
        # Create columns for better spacing
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Input for the journal entry with placeholder
            journal_entry = st.text_area(
                "Write your journal entry here:", 
                height=200, 
                placeholder="What's on your mind today?"
            )
            
            # Dynamic character count with color coding
            char_count = len(journal_entry)
            if char_count > 0:
                color = "green" if char_count <= 500 else "red"
                st.markdown(f"<p style='color:{color}'>Character Count: {char_count}</p>", 
                            unsafe_allow_html=True)
        
        with col2:
            # Entry submission and management
            st.write("### Journal Actions")
            
            # Submit entry button
            if st.button("💾 Save Entry", use_container_width=True):
                if journal_entry.strip():
                    # Get the current time and format it
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # Append the entry and timestamp to the session state
                    st.session_state.journal_entries.append((current_time, journal_entry))
                    st.success("Entry saved successfully!")
                     # Use st.rerun() instead of st.experimental_rerun()
                else:
                    st.error("Please write something before submitting!")
            
            # Clear entries with enhanced confirmation
            if st.button("🗑️ Clear All Entries", use_container_width=True):
                 if st.session_state.journal_entries:
                     if st.checkbox("Are you sure you want to clear all entries?"):
            # Directly clear the list of journal entries
                            st.session_state.journal_entries = []
                            st.success("All entries have been cleared!")
                            st.rerun()
                 else:
                     st.warning("No entries to clear.")

           
    
    # Search functionality with container
    with st.container():
        st.write("### Search Entries")
        search_term = st.text_input("Search your journal entries:")
        
        # Display journal entries with search filtering
        if st.session_state.journal_entries:
            filtered_entries = [
                entry for entry in st.session_state.journal_entries 
                if search_term.lower() in entry[1].lower()
            ]
            
            if filtered_entries:
                st.write("### Your Journal Entries")
                for time_sent, message in reversed(filtered_entries):
                    with st.expander(f"Entry from {time_sent}"):
                        st.write(message)
            else:
                st.info("No entries match your search term.")
        else:
            st.info("No journal entries yet. Start writing your first entry!")

def stress_burster():
    st.title("🧘 Stress Burster")
    
    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
    
    .spline-container {
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        overflow: hidden;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Introduction text
    st.markdown("""
    ### Take a Moment to Unwind 
    Interact with our BlueBall and let your stress melt away.
    """)
    
    # Spline Design Container
    st.markdown("""
    <div class="spline-container">
    <iframe 
        src='https://my.spline.design/aitherapist-e7816283ccca0cc7f2e74c543a304ec1/' 
        frameborder='0' 
        width='100%' 
        height='500px'>
    </iframe>
    </div>
    """, unsafe_allow_html=True)
    
    # Stress Relief Tips
    st.subheader("Quick Stress Relief Tips")
    tips = [
        "Take deep, slow breaths",
        "Practice mindfulness",
        "Stretch or do light exercise",
        "Listen to calming music"
    ]
    
    for tip in tips:
        st.markdown(f"• {tip}")

import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def mood_tracker_page():
    st.title("📊 Mood Tracker")
    
    # Initialize mood history in session state
    if 'mood_history' not in st.session_state:
        st.session_state.mood_history = []
    
    # Mood input section
    st.subheader("How are you feeling today?")
    
    # Create two columns for mood input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        mood_scale = st.slider("Rate your mood (1-10):", 1, 10, 5)
        mood_notes = st.text_area("Any notes about your mood?", placeholder="What's affecting your mood today?")
    
    with col2:
        mood_emojis = {
            1: "😢", 2: "😔", 3: "😕", 4: "😐",
            5: "😊", 6: "😄", 7: "😃", 8: "😁",
            9: "🤗", 10: "🥳"
        }
        st.markdown(f"### {mood_emojis[mood_scale]}")
        if st.button("Save Mood"):
            current_time = datetime.now()
            st.session_state.mood_history.append({
                'date': current_time,
                'mood': mood_scale,
                'notes': mood_notes
            })
            st.success("Mood recorded!")
    
    # Display mood history graph
    if st.session_state.mood_history:
        st.subheader("Your Mood History")
        
        # Convert mood history to DataFrame
        df = pd.DataFrame(st.session_state.mood_history)
        
        # Create line chart using plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['mood'],
            mode='lines+markers',
            name='Mood',
            line=dict(color='#236860'),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Mood Over Time',
            xaxis_title='Date',
            yaxis_title='Mood Level',
            yaxis_range=[0, 11],
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display mood entries
        st.subheader("Recent Entries")
        for entry in reversed(st.session_state.mood_history[-5:]):
            with st.expander(f"Entry from {entry['date'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(f"Mood: {entry['mood']}/10 {mood_emojis[entry['mood']]}")
                st.write(f"Notes: {entry['notes']}")

def gratitude_journal_page():
    st.title("🙏 Gratitude Journal")
    
    # Initialize gratitude entries in session state
    if 'gratitude_entries' not in st.session_state:
        st.session_state.gratitude_entries = []
    
    st.markdown("""
    ### Daily Gratitude Practice
    Taking time to appreciate the good things in life can improve mental well-being.
    """)
    
    # Create gratitude entry
    gratitude_text = st.text_area(
        "What are you grateful for today?",
        placeholder="List 3 things you're thankful for..."
    )
    
    if st.button("Save Gratitude Entry"):
        if gratitude_text.strip():
            current_time = datetime.now()
            st.session_state.gratitude_entries.append({
                'date': current_time,
                'entry': gratitude_text
            })
            st.success("Gratitude entry saved! 🌟")
    
    # Display gratitude history
    if st.session_state.gratitude_entries:
        st.subheader("Your Gratitude Journey")
        for entry in reversed(st.session_state.gratitude_entries):
            with st.expander(f"Entry from {entry['date'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(entry['entry'])

def sleep_tracker_page():
    st.title("😴 Sleep Tracker")
    
    # Initialize sleep data in session state
    if 'sleep_data' not in st.session_state:
        st.session_state.sleep_data = []
    
    # Sleep entry form
    st.subheader("Log Your Sleep")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sleep_date = st.date_input("Date:")
        sleep_duration = st.number_input("Hours of sleep:", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
    
    with col2:
        sleep_quality = st.select_slider(
            "Sleep quality:",
            options=["Poor", "Fair", "Good", "Very Good", "Excellent"],
            value="Good"
        )
        
        factors = st.multiselect(
            "Factors affecting sleep:",
            ["Stress", "Exercise", "Caffeine", "Screen Time", "Noise", "Temperature"]
        )
    
    if st.button("Save Sleep Log"):
        st.session_state.sleep_data.append({
            'date': sleep_date,
            'duration': sleep_duration,
            'quality': sleep_quality,
            'factors': factors
        })
        st.success("Sleep log saved!")
    
    # Display sleep statistics and graphs
    if st.session_state.sleep_data:
        st.subheader("Sleep Statistics")
        
        # Convert to DataFrame
        df = pd.DataFrame(st.session_state.sleep_data)
        
        # Create sleep duration chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['duration'],
            name='Sleep Duration',
            marker_color='#236860'
        ))
        
        fig.update_layout(
            title='Sleep Duration Over Time',
            xaxis_title='Date',
            yaxis_title='Hours of Sleep',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display average sleep statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Sleep Duration", f"{df['duration'].mean():.1f} hours")
        with col2:
            st.metric("Most Common Quality", df['quality'].mode()[0])

def resources_page():
    st.title("🆘 Mental Health Resources")
    
    # Emergency Contacts
    st.header("Emergency Contacts")
    
    emergency_contacts = {
        "National Crisis Hotline": "1-800-273-8255",
        "Crisis Text Line": "Text HOME to 741741",
        "Emergency Services": "911"
    }
    
    for service, contact in emergency_contacts.items():
        st.markdown(f"**{service}**: {contact}")
    
    # Mental Health Resources
    st.header("Self-Help Resources")
    
    with st.expander("Meditation Apps"):
        st.markdown("""
        - Headspace
        - Calm
        - Insight Timer
        - Simple Habit
        """)
    
    with st.expander("Educational Resources"):
        st.markdown("""
        - National Institute of Mental Health
        - Mental Health America
        - Psychology Today
        - Mind.org
        """)
    
    with st.expander("Support Groups"):
        st.markdown("""
        - NAMI Support Groups
        - Depression and Bipolar Support Alliance
        - Anxiety and Depression Association of America
        """)
    
    # Mental Health Tips
    st.header("Quick Mental Health Tips")
    
    tips = [
        "Practice deep breathing exercises",
        "Maintain a regular sleep schedule",
        "Exercise regularly",
        "Stay connected with loved ones",
        "Practice mindfulness",
        "Set realistic goals",
        "Take breaks when needed"
    ]
    
    for tip in tips:
        st.markdown(f"• {tip}")

def brainrot_corner_page():
    st.header("🎮 Brainrot Corner")

    if 'meme_counter' not in st.session_state:
        st.session_state.meme_counter = 0

    def fetch_random_meme():
        try:
            # Fetch meme from a working API
            response = requests.get("https://meme-api.com/gimme", timeout=10)  # Use a valid API
            response.raise_for_status()
            meme_data = response.json()
            # Check the API response structure
            image_url = meme_data.get('url', "https://via.placeholder.com/800x600")
            meme_text = meme_data.get('title', "No caption available.")
            return image_url, meme_text
        except requests.exceptions.RequestException as e:
            # Handle API errors gracefully
            st.error(f"Error fetching meme: {e}")
            return "https://via.placeholder.com/800x600", "Error fetching meme! Try again."

    if st.button("Generate New Meme"):
        st.session_state.meme_counter += 1
        image_url, meme_text = fetch_random_meme()

        # Display the fetched meme
        st.markdown(f"""
            <div style="text-align: center; background-color: #1a1a1a; padding: 20px; border-radius: 10px; margin: 10px 0;">
                <h2 style="color: white; font-size: 24px; margin-bottom: 20px;">{meme_text}</h2>
                <img src="{image_url}" style="max-width: 100%; border-radius: 8px;" alt="Random Meme">
                <p style="color: #888; margin-top: 15px;">Meme #{st.session_state.meme_counter}</p>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.meme_counter % 5 == 0:
            st.balloons()
            st.markdown("""
                <div style="text-align: center; color: #236860; font-size: 20px; margin: 20px 0;">
                    🎉 Milestone reached! Keep the memes flowing! 🎉
                </div>
            """, unsafe_allow_html=True)

    # Footer with meme counter
    st.markdown(f"""
        <div style="text-align: center; margin-top: 20px; color: #888;">
            Memes Generated: {st.session_state.meme_counter} 🎭
            <br>Keep clicking for infinite entertainment!
        </div>
    """, unsafe_allow_html=True)


def therapeutic_activities_page():


    # Get the absolute path to the assets directory
    assets_dir = Path(__file__).parent / "assets"
    audio_dir = assets_dir / "audio"

    st.title("🎨 Therapeutic Activities")
    
    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
    .activity-card {
        background: linear-gradient(145deg, #ffffff, #f0f0f0);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .activity-card:hover {
        transform: translateY(-5px);
    }
    .canvas-container {
        background: white;
        border-radius: 10px;
        padding: 10px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
    }
    .visualization-text {
        font-size: 1.2em;
        line-height: 1.6;
        padding: 20px;
        background: rgba(255,255,255,0.9);
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Activities Selection
    activity = st.selectbox(
        "Choose an Activity:",
        ["Art Therapy", "Guided Visualization", "Sound Therapy", "Color Therapy"]
    )

    if activity == "Art Therapy":
        st.subheader("🎨 Express Yourself Through Art")
        
        # Initialize session state for art therapy
        if 'drawing_mode' not in st.session_state:
            st.session_state.drawing_mode = "freedraw"
        if 'stroke_width' not in st.session_state:
            st.session_state.stroke_width = 2
        if 'stroke_color' not in st.session_state:
            st.session_state.stroke_color = "#000000"
        
        # Art tools
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            st.session_state.drawing_mode = st.selectbox(
                "Drawing Tool:",
                ("freedraw", "line", "rect", "circle")
            )
        with col2:
            st.session_state.stroke_width = st.slider("Brush Size:", 1, 25, 2)
        with col3:
            st.session_state.stroke_color = st.color_picker("Color:", "#000000")
        
        # Canvas for drawing
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=st.session_state.stroke_width,
            stroke_color=st.session_state.stroke_color,
            background_color="#FFFFFF",
            background_image=None,
            update_streamlit=True,
            height=400,
            drawing_mode=st.session_state.drawing_mode,
            key="canvas",
        )

    elif activity == "Guided Visualization":
        st.subheader("🌿 Peaceful Visualization Journey")
        
        scenes = {
            "Beach Relaxation": """
            Close your eyes and take a deep breath.
            Imagine yourself on a peaceful beach.
            The warm sun gently touches your skin.
            You hear the rhythmic sounds of waves.
            Feel the soft sand beneath you.
            Take a deep breath of the fresh ocean air.
            Let the peaceful sounds of the waves calm your mind.
            Feel yourself becoming more relaxed with each breath.
            """,
            "Forest Meditation": """
            Close your eyes and take a deep breath.
            You're walking through a serene forest.
            Sunlight filters through the leaves above.
            Listen to the gentle rustling of leaves in the breeze.
            Birds are singing in the distance.
            Feel the cool, fresh air fill your lungs.
            Each step connects you more deeply with nature.
            Let the peaceful forest energy surround you.
            """,
            "Mountain Sanctuary": """
            Close your eyes and take a deep breath.
            You're standing on a majestic mountain peak.
            The air is crisp and clean.
            Fluffy white clouds float by at eye level.
            A gentle breeze carries the scent of pine.
            Feel the strength of the mountain beneath your feet.
            Let the mountain's stability ground you.
            Breathe in the pure mountain air.
            """
        }
        
        selected_scene = st.selectbox("Choose your visualization:", list(scenes.keys()))
        
        # Voice selection
        voice_options = {
            "Default": "en",
            "British": "en-gb",
            "Australian": "en-au",
            "Indian": "en-in",
            "US": "en-us"
        }
        
        voice = st.selectbox("Choose a voice:", list(voice_options.keys()))
        
        if st.button("Begin Visualization"):
            # Create a progress bar
            progress = st.progress(0)
            status_text = st.empty()
            
            # Split the text into lines and remove empty lines
            lines = [line.strip() for line in scenes[selected_scene].split('\n') if line.strip()]
            
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_path = fp.name
                
                # Convert each line to speech
                for i, line in enumerate(lines):
                    # Update progress
                    progress.progress((i + 1) / len(lines))
                    status_text.text(f"Playing: {line}")
                    
                    # Generate speech for the current line
                    tts = gTTS(text=line, lang=voice_options[voice], slow=True)
                    tts.save(temp_path)
                    
                    # Display the text
                    st.markdown(f'<div class="visualization-text">{line}</div>', 
                              unsafe_allow_html=True)
                    
                    # Play the audio
                    with open(temp_path, 'rb') as audio_file:
                        st.audio(audio_file.read(), format='audio/mp3')
                        time.sleep(1)  # Small pause between lines
            
            # Clean up the temporary file
            os.unlink(temp_path)
            
            # Complete
            progress.progress(100)
            status_text.text("Visualization complete")
            st.success("Visualization session complete. Take a moment to reflect.")

    elif activity == "Sound Therapy":
        st.subheader("🎵 Therapeutic Sounds")
        
        # Sound options with file paths
        sounds = {
            "Ocean Waves": audio_dir / "ocean.mp3",
            "Forest Birds": audio_dir / "forest.mp3",
            "Rainfall": audio_dir / "rain.mp3"
        }
        
        col1, col2 = st.columns(2)
        with col1:
            selected_sound = st.selectbox("Choose a sound:", list(sounds.keys()))
            
        with col2:
            st.markdown("### Sound Settings")
            volume = st.slider("Volume:", 0.0, 1.0, 0.5)
            
        if st.button("Play Sound"):
            try:
                with open(sounds[selected_sound], "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/mp3")
            except FileNotFoundError:
                st.error(f"Audio file for {selected_sound} not found. Please ensure it exists in the assets directory.")

    elif activity == "Color Therapy":
        st.subheader("🌈 Chromotherapy Session")
        
        # Color therapy information
        color_info = {
            "Red": {"emotion": "Energy & Vitality", "healing": "Stimulates and energizes"},
            "Blue": {"emotion": "Calm & Serenity", "healing": "Promotes relaxation"},
            "Green": {"emotion": "Balance & Harmony", "healing": "Supports healing"},
            "Yellow": {"emotion": "Joy & Clarity", "healing": "Boosts mood"},
            "Purple": {"emotion": "Spirituality", "healing": "Enhances meditation"},
        }
        
        # Color selection
        selected_color = st.select_slider(
            "Choose a color for your therapy session:",
            options=list(color_info.keys())
        )
        
        # Display color information
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### {selected_color} Energy")
            st.markdown(f"**Emotional Association:** {color_info[selected_color]['emotion']}")
            st.markdown(f"**Healing Properties:** {color_info[selected_color]['healing']}")
        
        with col2:
            # Display color box
            st.markdown(f"""
                <div style="
                    background-color: {selected_color.lower()};
                    width: 100%;
                    height: 200px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                "></div>
            """, unsafe_allow_html=True)



def main():
    init_styles()


    # Create columns to put image and title on the same line
    col1, col2 = st.columns([1.5, 10])  # Adjust column proportions as needed

    with col1:
        st.image('logo-no-bg.png', width=100)  # Smaller width to fit inline

    with col2:
        st.title("Talk Tuah Therapist")
        st.markdown("*Your Safe Space for Healing: Chat, Journal, Grow.*")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "Chatbot", "Breathing Center", "Journal Center",
        "Sleep Tracker", "Mood Tracker", "Stress Burster", 
        "Game Center", "BrainRot Memes", "Therapeutic Activities"
    ])

    with tab1:
        chatbot_page()
    with tab2:
        breathing_center_page()
    with tab3:
        journal_page()
    with tab4:
        sleep_tracker_page()
    with tab5:  
        mood_tracker_page()
    with tab6:
        stress_burster()
    with tab7:
        game_center_page()
    with tab8:
        brainrot_corner_page()
    with tab9:
        therapeutic_activities_page()


    # Add Resources section in sidebar
    with st.sidebar:
        st.title("Additional Resources")
        if st.button("View Mental Health Resources"):
            resources_page()

    st.markdown("""
    <hr>
    <p style='text-align: center; color: #888;'>Created with ❤ for mental health awareness</p>
    """, unsafe_allow_html=True)
if __name__=="__main__":
        main()
