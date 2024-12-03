import streamlit as st
import speech_recognition as sr
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
from gtts import gTTS

# Initialize the recognizer
recognizer = sr.Recognizer()

# Constants for Clarifai API
PAT = 'c11c44788d1f478dbf3a43ed4b39bd5b'  # Replace with your actual PAT
USER_ID = 'anthropic'
APP_ID = 'completion'
MODEL_ID = 'claude-3-opus'
MODEL_VERSION_ID = '0b59b93d35864b9b88699a557629babf'

# Function to generate chatbot response
def generate_response(user_message):
    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)

    metadata = (('authorization', 'Key ' + PAT),)
    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

    post_model_outputs_response = stub.PostModelOutputs(
        service_pb2.PostModelOutputsRequest(
            user_app_id=userDataObject,
            model_id=MODEL_ID,
            version_id=MODEL_VERSION_ID,
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        text=resources_pb2.Text(
                            raw=user_message
                        )
                    )
                )
            ]
        ),
        metadata=metadata
    )

    if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
        raise Exception(f"Post model outputs failed, status: {post_model_outputs_response.status.description}")

    output = post_model_outputs_response.outputs[0]
    return output.data.text.raw

# Function to record audio and transcribe it
def record_and_transcribe():
    with sr.Microphone() as source:
        st.write("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source)
        
        st.write("Listening... Please speak something.")
        audio_data = recognizer.listen(source)
        
        st.write("Recording complete.")
        
        try:
            st.write("Transcribing...")
            transcription = recognizer.recognize_google(audio_data)
            return transcription
        except sr.UnknownValueError:
            st.error("Sorry, I could not understand the audio.")
            return None
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Speech Recognition service; {e}")
            return None

# Function to convert text to speech and return audio file path
def speak(text):
    tts = gTTS(text=text, lang='en')  # Ensure lang is set to 'en' for English
    audio_file = "response.mp3"
    tts.save(audio_file)
    return audio_file

# Streamlit UI setup
st.set_page_config(page_title="Audio Transcription and Chatbot", page_icon=":thought_balloon:", layout="wide")
st.title("🗣 Audio Transcription and Mental Health Chatbot")
st.subheader("Record your voice and get empathetic responses!")

# Inject custom CSS for styling
st.markdown("""
<style>
body {
    font-family: 'Arial', sans-serif;
    background-color: whitesmoke;
    color: #333;
}

h1 {
    font-size: 48px;
    color: #A5B5F5;
    text-align: center;
}

h2 {
    font-size: 32px;
    color: #4A4A4A;
    text-align: center;
}

.stButton > button {
    background-color: #FF6F61;
    color: white;
    padding: 10px 20px;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    width: 100%;
    max-width: 300px;
    margin-top: 20px;
}

.stButton > button:hover {
    background-color: #A5B5F5;
}

.stButton > button:active {
    background-color: #D84F45;
}

.stTextInput {
    margin-top: 20px;
}

.stAudio {
    margin-top: 20px;
    display: block;
    margin-left: auto;
    margin-right: auto;
}

.stError {
    color: #D74E62;
}

.stSuccess {
    color: #4BB543;
}

</style>
""", unsafe_allow_html=True)

# State management for recording control and chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Function to handle recording
def start_recording():
    transcription = record_and_transcribe()
    
    if transcription:
        st.success("Transcription complete!")
        st.write("You said: " + transcription)

        # Send the transcribed text to the chatbot model
        try:
            response = generate_response(transcription)
            st.success("Chatbot response:")
            
            # Store messages in session state for display
            st.session_state.messages.append({"role": "user", "content": transcription})
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Speak out the chatbot's response and play it back in Streamlit
            audio_file_path = speak(response)
            st.audio(audio_file_path)  # Play the audio file directly in Streamlit
            
        except Exception as e:
            st.error(f"Error generating response: {e}")

# Start Recording Button
if st.button("Start Recording"):
    start_recording()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input for user to type messages directly (optional)
if prompt := st.chat_input("Type your message here..."):
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Process the typed message similarly if needed (optional)
    response = generate_response(prompt)  # Generate response from the chatbot
    
    with st.chat_message("assistant"):
        st.markdown(response)

# Footer message for better clarity



if __name__ == "__main__":
    st.write("Press the button to start recording your voice.")