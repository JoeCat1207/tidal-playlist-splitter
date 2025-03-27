#!/usr/bin/env python3
"""
Tidal Playlist Splitter

This script allows you to split a Tidal playlist into multiple segments
and create new playlists with those segments.
"""

import argparse
import sys
import re
from math import ceil
import time

try:
    import tidalapi
except ImportError:
    print("Error: tidalapi module not found. Please install it with 'pip install tidalapi'", file=sys.stderr)
    sys.exit(1)

def extract_playlist_id(url):
    """
    Extract the playlist ID from a Tidal playlist URL.
    """
    # Try different URL patterns
    patterns = [
        r'playlist/([a-zA-Z0-9-]+)',  # Standard format
        r'playlists/([a-zA-Z0-9-]+)'  # Alternative format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError("Could not extract playlist ID from URL. Expected format: https://listen.tidal.com/playlist/[playlist_id]")

def split_playlist(tracks, num_segments):
    """
    Split a list of tracks into approximately equal segments.
    """
    if not tracks:
        return []
    
    segment_size = ceil(len(tracks) / num_segments)
    segments = []
    
    for i in range(0, len(tracks), segment_size):
        segments.append(tracks[i:i + segment_size])
    
    return segments

def main():
    """Main function to execute the script."""
    parser = argparse.ArgumentParser(description='Split a Tidal playlist into segments and create new playlists.')
    parser.add_argument('playlist_url', help='URL of the Tidal playlist to split')
    parser.add_argument('--segments', type=int, default=2, help='Number of segments to split the playlist into (default: 2)')
    parser.add_argument('--prefix', default='Segment', help='Prefix for the new playlist names (default: "Segment")')
    parser.add_argument('--naming-pattern', default='{prefix} {index} - {playlist}', 
                        help='Pattern for naming new playlists. Available variables: {prefix}, {index}, {playlist}, {total}')
    parser.add_argument('--description-pattern', default='Segment {index} of {total} from {playlist}',
                        help='Pattern for playlist descriptions. Available variables: {index}, {total}, {playlist}')
    args = parser.parse_args()
    
    # Validate input
    if args.segments < 1:
        print("Error: Number of segments must be at least 1", file=sys.stderr)
        return 1
    
    # Extract playlist ID from URL
    try:
        playlist_id = extract_playlist_id(args.playlist_url)
        print(f"Extracted playlist ID: {playlist_id}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Initialize Tidal session - exactly as tidallister.py does
    config = tidalapi.Config()
    session = tidalapi.Session(config)
    
    # Handle login exactly the same way as tidallister.py
    print("\nLogging in to Tidal...")
    try:
        # Use the exact same approach as tidallister.py
        login, future = session.login_oauth()
        
        # Print the login URL
        print(f"Visit {login.verification_uri_complete} to log in, the code will expire in {login.expires_in} seconds")
        
        # Call login_oauth_simple which seems to be needed for the process to work
        session.login_oauth_simple()
        
        # Wait for authentication by repeatedly checking login status
        print("Waiting for authentication...")
        timeout = login.expires_in
        start_time = time.time()
        
        # Keep checking until we're logged in or time out
        while not session.check_login():
            if time.time() - start_time > timeout:
                print("Login timed out. Please try again.")
                return 1
            time.sleep(2)  # Check every 2 seconds
        
        print(f"Logged in successfully as {session.user.username}")
        
    except Exception as e:
        print(f"Error during login: {e}", file=sys.stderr)
        return 1
    
    # Get the source playlist
    try:
        print(f"\nFetching playlist with ID: {playlist_id}")
        # Use playlist() method as in tidallister.py
        source_playlist = session.playlist(playlist_id)
        print(f"Found playlist: {source_playlist.name}")
        
        # Get tracks using tracks() method
        print("Fetching tracks...")
        tracks_list = list(source_playlist.tracks())
        print(f"Playlist has {len(tracks_list)} tracks")
        
    except Exception as e:
        print(f"Error retrieving playlist: {e}", file=sys.stderr)
        return 1
    
    if not tracks_list:
        print("Error: Playlist has no tracks", file=sys.stderr)
        return 1
    
    # Split the tracks into segments
    segments = split_playlist(tracks_list, args.segments)
    print(f"\nSplit playlist into {len(segments)} segments")
    
    # Create new playlists
    for i, segment in enumerate(segments, 1):
        # Format the playlist name and description using the provided patterns
        context = {
            'prefix': args.prefix,
            'index': i,
            'total': len(segments),
            'playlist': source_playlist.name
        }
        
        new_playlist_name = args.naming_pattern.format(**context)
        new_playlist_description = args.description_pattern.format(**context)
        
        # Truncate if too long (Tidal might have a name length limit)
        if len(new_playlist_name) > 50:
            new_playlist_name = f"{args.prefix} {i} - {source_playlist.name[:40]}..."
        
        try:
            # Create new playlist - using the exact same approach as tidallister.py
            print(f"\nCreating playlist '{new_playlist_name}'...")
            new_playlist = session.user.create_playlist(new_playlist_name, new_playlist_description)
            
            # Get track IDs for adding to the playlist
            track_ids = [track.id for track in segment]
            
            # Add tracks using add() method as in tidallister.py
            print(f"Adding {len(segment)} tracks to the new playlist...")
            new_playlist.add(track_ids)
            
            print(f"Created playlist '{new_playlist_name}' with {len(segment)} tracks")
            print(f"Playlist URL: https://tidal.com/browse/playlist/{new_playlist.id}")
            
        except Exception as e:
            print(f"Error creating segment {i}: {e}", file=sys.stderr)
    
    print("\nDone! All playlist segments have been created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())