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

def get_all_tracks(playlist, session):
    """
    Get all tracks from a playlist with pagination handling.
    """
    all_tracks = []
    page_size = 100  # Fetch 100 tracks at a time
    offset = 0
    
    print("Fetching playlist tracks (this may take a while for large playlists)...")
    
    while True:
        try:
            # Try to get tracks with pagination parameters if the API supports it
            if hasattr(playlist, 'items') and callable(playlist.items):
                # Some versions support offset/limit parameters
                try:
                    tracks_page = list(playlist.items(offset=offset, limit=page_size))
                except TypeError:
                    # If parameters aren't supported, fall back to default method
                    if offset == 0:  # Only do this once
                        tracks_page = list(playlist.items())
                    else:
                        break  # We've already fetched all we can
            elif hasattr(playlist, 'tracks') and callable(playlist.tracks):
                try:
                    tracks_page = list(playlist.tracks(offset=offset, limit=page_size))
                except TypeError:
                    if offset == 0:
                        tracks_page = list(playlist.tracks())
                    else:
                        break
            else:
                # Last resort - try to access tracks as a property
                if offset == 0:  # Can only do this once
                    tracks_page = list(playlist.tracks)
                else:
                    break
            
            # If we got an empty page or fewer items than requested, we're done
            if not tracks_page:
                break
                
            all_tracks.extend(tracks_page)
            print(f"Fetched {len(all_tracks)} tracks so far...")
            
            # If we got fewer items than the page size, we've reached the end
            if len(tracks_page) < page_size:
                break
                
            # Move to the next page
            offset += page_size
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error while fetching tracks at offset {offset}: {e}")
            # Try to continue with what we have
            break
    
    return all_tracks

def add_tracks_with_retry(playlist, track_ids, batch_size=50):
    """
    Add tracks to a playlist in batches with retry logic.
    """
    total_tracks = len(track_ids)
    tracks_added = 0
    
    for i in range(0, total_tracks, batch_size):
        batch = track_ids[i:i+batch_size]
        retries = 3
        success = False
        
        while retries > 0 and not success:
            try:
                playlist.add(batch)
                success = True
                tracks_added += len(batch)
                print(f"Added batch of {len(batch)} tracks ({tracks_added}/{total_tracks})")
            except Exception as e:
                retries -= 1
                print(f"Error adding tracks: {e}, retries left: {retries}")
                if retries > 0:
                    print("Waiting 5 seconds before retrying...")
                    time.sleep(5)
        
        if not success:
            print(f"Failed to add batch starting at track {i} after multiple retries")
        
        # Add a small delay between successful batches to avoid rate limiting
        time.sleep(1)
    
    return tracks_added

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
    parser.add_argument('--batch-size', type=int, default=50, 
                       help='Number of tracks to add in a single batch (default: 50)')
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
    
    # Initialize Tidal session
    config = tidalapi.Config()
    session = tidalapi.Session(config)
    
    # Handle login 
    print("\nLogging in to Tidal...")
    try:
        # Use the login_oauth method
        login, future = session.login_oauth()
        
        # Print the login URL
        print(f"Visit {login.verification_uri_complete} to log in, the code will expire in {login.expires_in} seconds")
        
        # Call login_oauth_simple which seems to be needed for the process to work
        session.login_oauth_simple()
        
        # Wait for authentication
        print("Waiting for authentication...")
        timeout = login.expires_in
        start_time = time.time()
        
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
        source_playlist = session.playlist(playlist_id)
        print(f"Found playlist: {source_playlist.name}")
        
        # Get all tracks with pagination handling
        tracks_list = get_all_tracks(source_playlist, session)
        
        print(f"Successfully retrieved all {len(tracks_list)} tracks")
        
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
            # Create new playlist
            print(f"\nCreating playlist '{new_playlist_name}'...")
            new_playlist = session.user.create_playlist(new_playlist_name, new_playlist_description)
            
            # Get track IDs for adding to the playlist
            track_ids = [track.id for track in segment]
            
            # Add tracks in batches with retry logic
            print(f"Adding {len(segment)} tracks to the new playlist...")
            tracks_added = add_tracks_with_retry(new_playlist, track_ids, args.batch_size)
            
            # Check if all tracks were added successfully
            if tracks_added == len(segment):
                print(f"Created playlist '{new_playlist_name}' with all {len(segment)} tracks")
            else:
                print(f"Created playlist '{new_playlist_name}' but only added {tracks_added}/{len(segment)} tracks")
            
            print(f"Playlist URL: https://tidal.com/browse/playlist/{new_playlist.id}")
            
            # Small delay between creating playlists to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"Error creating segment {i}: {e}", file=sys.stderr)
    
    print("\nDone! All playlist segments have been created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())