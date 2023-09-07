import streamlit as st
import spotipy
import sqlite3
from spotipy.oauth2 import SpotifyOAuth
# Set up Spotify API credentials and scope

client_id = "ac9f788a554b47418cb1eb398d0e33ae"
client_secret = "b44d5a71c1624246995e12c76cf8e899"
redirect_uri = "https://objective-bangers.streamlit.app/" # This should match the redirect URI in your Spotify developer dashboard
scope = ["playlist-modify-private", "playlist-modify-public"]

conn = sqlite3.connect("songs.db")
c = conn.cursor()

# Create a table for songs if it does not exist
c.execute("""CREATE TABLE IF NOT EXISTS songs (
    track_name TEXT,
    artist TEXT,
    uri TEXT PRIMARY KEY,
    bangs TEXT,
    does_not_bang TEXT,
    added BOOL
)""")

# Create a SpotifyOAuth object
sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope)

# Create a Streamlit app
st.title("Streamlit Spotify Login Example")

# Check if the user has already authenticated
access_token = st.session_state.get('access_token')
if access_token:
    # If yes, create a Spotify client and display the user's profile
    sp = spotipy.Spotify(access_token)
    user = sp.current_user()
    print(user)
    st.write(f"Welcome, {user['display_name']}!")
    # Display text input for song name
    song_name = st.text_input("Enter a song name")

    # Search for song on Spotify using Spotipy
    if song_name:
        results = sp.search(q=song_name, limit=5)
        tracks = results["tracks"]["items"]
        if tracks:
            # Display radio button for song results
            options = [f"{track['name']} by {track['artists'][0]['name']}" for track in tracks]
            choice = st.radio("Select a song", options)
            index = options.index(choice)
            track = tracks[index]

            if st.button("Bangs"):
                c.execute("SELECT * FROM songs WHERE uri = ?", (track["uri"],))
                row = c.fetchone()
                if row:
                    # Update the bangs column by adding the user name
                    bangs_list = row[3].split(",") # Convert the string to a list
                    does_not_bang_list = row[4].split(" ") # Convert the string to a list
                    if user["display_name"] not in bangs_list and user["display_name"] not in does_not_bang_list: # Check if the user has not voted before
                        bangs_list.append(user["display_name"]) # Add the user name to the list
                        bangs_string = ",".join(bangs_list) # Convert the list back to a string
                        c.execute("UPDATE songs SET bangs = ? WHERE uri = ?", (bangs_string, track["uri"]))
                        st.success(f"Your vote for {choice} has been added")
                else:
                    # Insert a new row with the song information and the user name as bangs
                    c.execute("INSERT INTO songs VALUES (?, ?, ?, ?, '', ?)", (track["name"], track['artists'][0]['name'], track["uri"], user["display_name"], False))
                    st.success(f"Your vote for {choice} has been added")
                conn.commit()

            if st.button("Does Not Bang"):
                # Check if the song is already in the database
                c.execute("SELECT * FROM songs WHERE uri = ?", (track["uri"],))
                row = c.fetchone()
                if row:
                    # Update the does_not_bang column by adding the user name
                    bangs_list = row[3].split(",") # Convert the string to a list
                    does_not_bang_list = row[4].split(" ") # Convert the string to a list
                    if user["display_name"] not in bangs_list and user["display_name"] not in does_not_bang_list: # Check if the user has not voted before
                        does_not_bang_list.append(user["display_name"]) # Add the user name to the list
                        does_not_bang_string = " ".join(does_not_bang_list) # Convert the list back to a string
                        c.execute("UPDATE songs SET does_not_bang = ? WHERE uri = ?", (does_not_bang_string, track["uri"]))
                        st.success(f"Your vote for {choice} has been added")
                conn.commit()
            

            # Display button to create playlist from songs with more than 3 votes using Spotipy

            c.execute("SELECT * FROM songs WHERE uri = ?", (track["uri"],))
            row = c.fetchone()
            if row:
                if len(row[3].split(",")) == 2 and not row[5] and user["display_name"] == "joejbailey-gb":
                    # Create playlist on Spotify using Spotipy
                    playlist_name = "objective bangers"

                    playlist = sp.playlist("https://open.spotify.com/playlist/27umP85d8CGU0hfMW7Vpcf")
                    
                    #if playlist['name'] == playlist_name:
                    # Add songs to playlist using Spotipy
                    sp.user_playlist_add_tracks(user['id'], playlist['id'], [track["uri"]])
                    st.success(f"{track['name']} by {track['artists'][0]['name']} was added to Objective Bangers")
                            
                    c.execute("UPDATE songs SET added = ? WHERE uri = ?", (True, track["uri"]))
                    conn.commit()


    # Display table with song suggestions and votes from database using Streamlit
    c.execute("SELECT * FROM songs")
    songs = c.fetchall()
    st.table(songs)

            
else:
    # If not, display a button that redirects to the Spotify login page
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f"[Login with Spotify]({auth_url})")

    # Get the authorization code from the callback URL
    args = st.experimental_get_query_params()
    code = args.get('code')

    # If the code exists, exchange it for an access token and store it in the session state
    if code:
        token_info = sp_oauth.get_access_token(code[0])
        access_token = token_info['access_token']
        st.session_state['access_token'] = access_token
        # Reload the page to display the user's profile
        st.experimental_rerun()
