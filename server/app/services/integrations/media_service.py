import spotipy
from spotipy.oauth2 import SpotifyOAuth
import google_auth_oauthlib.flow
import googleapiclient.discovery
from typing import Dict, Any, Optional
from ...config import settings
from ...core.logging import setup_logging

logger = setup_logging()

class MediaService:
    def __init__(self):
        self._init_spotify()
        self._init_youtube()

    def _init_spotify(self):
        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope="user-modify-playback-state user-read-playback-state"
        ))

    def _init_youtube(self):
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            settings.YOUTUBE_CLIENT_SECRETS_FILE,
            ["https://www.googleapis.com/auth/youtube"]
        )
        credentials = flow.run_local_server(port=0)
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=credentials
        )

    async def control_spotify(
        self, 
        action: str, 
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            if action == "play":
                if query:
                    results = self.spotify.search(query, limit=1)
                    if results["tracks"]["items"]:
                        track_uri = results["tracks"]["items"][0]["uri"]
                        self.spotify.start_playback(uris=[track_uri])
                else:
                    self.spotify.start_playback()
            elif action == "pause":
                self.spotify.pause_playback()
            elif action == "next":
                self.spotify.next_track()
            elif action == "previous":
                self.spotify.previous_track()

            return {"status": "success", "action": action}
        except Exception as e:
            logger.error(f"Spotify control failed: {str(e)}")
            raise

    async def control_youtube_music(
        self, 
        action: str, 
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            if action == "search" and query:
                request = self.youtube.search().list(
                    part="snippet",
                    maxResults=1,
                    q=query,
                    type="video"
                )
                response = request.execute()
                return {
                    "status": "success",
                    "video_id": response["items"][0]["id"]["videoId"]
                }

            return {"status": "success", "action": action}
        except Exception as e:
            logger.error(f"YouTube Music control failed: {str(e)}")
            raise
