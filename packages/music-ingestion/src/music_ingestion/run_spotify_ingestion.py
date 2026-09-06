import os

from dotenv import load_dotenv

from music_ingestion.spotify_client import SpotifyClient

load_dotenv()

access_token = os.getenv("SPOTIFY_ACCESS_TOKEN")

if not access_token:
    raise ValueError("SPOTIFY_ACCESS_TOKEN is missing")

client = SpotifyClient(access_token)

top_artists = client.get_top_artists()
top_tracks = client.get_top_tracks()
recently_played = client.get_recently_played()

print("\nTOP ARTISTS:")

for i, artist in enumerate(top_artists["items"], start=1):
    print(f"{i}. {artist['name']}")

print("\n TOP TRACKS :")

for i, track in enumerate(top_tracks["items"], start=1):
    print(f"{i}. {track['name']} - {track['artists'][0]['name']}")

print("\nRECENTLY PLAYED:")

for i, item in enumerate(recently_played["items"], start=1):
    track = item["track"]
    print(f"{i}. {track['name']} - {track['artists'][0]['name']}")