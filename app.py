import streamlit as st

# Try importing yt-dlp with error handling for debugging
try:
    import yt_dlp
except ImportError as e:
    st.error(f"❌ Failed to import yt-dlp: {e}")
    st.error("Please make sure yt-dlp is installed. Contact support if this issue persists.")
    st.stop()

import os
import re
import threading
import time
from pathlib import Path
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="YouTube Playlist Downloader",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #FF0000, #CC0000, #FF6B6B);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(255, 0, 0, 0.3);
    }
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #FF0000;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    .success-message {
        background: linear-gradient(90deg, #d4edda, #c3e6cb);
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .error-message {
        background: linear-gradient(90deg, #f8d7da, #f5c6cb);
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .info-box {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
    }
    .info-box h3 {
        margin-top: 0;
        color: #1976d2;
        font-weight: 600;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #FF0000, #FF6B6B, #CC0000);
        border-radius: 10px;
    }
    .quick-action-btn {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 0.2rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .quick-action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }
    .download-stats {
        background: linear-gradient(135deg, #fff3e0, #ffe0b2);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff9800;
        margin: 1rem 0;
    }
    .video-preview {
        background: #fafafa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
    .stSelectbox > div > div {
        border-radius: 8px;
    }
    .stTextInput > div > div {
        border-radius: 8px;
    }
    .stButton > button {
        border-radius: 10px;
        border: none;
        background: linear-gradient(135deg, #FF0000, #CC0000);
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 0, 0, 0.3);
    }
    .sidebar .stSelectbox > div > div {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

def validate_url(url):
    """Validate YouTube URL for both playlists and single videos."""
    if not url:
        return False, "URL cannot be empty", None
    
    # Patterns for both playlists and single videos
    playlist_patterns = [
        r'^https?://(www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+&list=[\w-]+',
        r'^https?://youtu\.be/[\w-]+\?list=[\w-]+'
    ]
    
    single_video_patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://youtu\.be/[\w-]+'
    ]
    
    for pattern in playlist_patterns:
        if re.match(pattern, url):
            return True, "Valid playlist URL", "playlist"
    
    for pattern in single_video_patterns:
        if re.match(pattern, url):
            return True, "Valid video URL", "video"
    
    return False, "Please enter a valid YouTube URL (video or playlist)", None

def get_content_info(url):
    """Get information for both videos and playlists with preview."""
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': False,  # Get detailed info for preview
            'no_warnings': True,
            # Add headers to avoid bot detection
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            # Add cookies and additional options to avoid detection
            'cookiesfrombrowser': None,
            'sleep_interval': 1,  # Add delay between requests
            'max_sleep_interval': 5,
            'sleep_interval_subtitles': 1,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check if it's a playlist or single video
            if 'entries' in info and info['entries']:
                # It's a playlist
                entries = list(info['entries'])
                return {
                    'type': 'playlist',
                    'title': info.get('title', 'Unknown Playlist'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'count': len(entries),
                    'description': info.get('description', ''),
                    'preview_videos': entries[:3],  # First 3 videos for preview
                    'duration_total': sum(entry.get('duration', 0) for entry in entries if entry.get('duration')),
                    'view_count': info.get('view_count', 0)
                }
            else:
                # It's a single video
                return {
                    'type': 'video',
                    'title': info.get('title', 'Unknown Video'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'like_count': info.get('like_count', 0),
                    'tags': info.get('tags', [])[:5]  # First 5 tags
                }
    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            st.warning("⚠️ YouTube is currently blocking requests from this server. This is a temporary issue that may resolve itself. Please try again later or use a different video URL.")
            return None
        else:
            st.error(f"Error fetching content info: {error_msg}")
            return None

def format_duration(seconds):
    """Convert seconds to readable duration format."""
    if not seconds:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def format_number(num):
    """Format large numbers with K, M, B suffixes."""
    if not num:
        return "0"
    
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(num)

def get_available_formats(url):
    """Get available formats for a video/playlist to show quality options."""
    try:
        ydl_opts = {
            'quiet': True,
            'listformats': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            # Extract unique video qualities
            video_qualities = set()
            audio_qualities = set()
            
            for fmt in formats:
                if fmt.get('vcodec') != 'none':  # Video format
                    height = fmt.get('height')
                    if height:
                        video_qualities.add(height)
                elif fmt.get('acodec') != 'none':  # Audio format
                    abr = fmt.get('abr')
                    if abr:
                        audio_qualities.add(abr)
            
            return {
                'video_qualities': sorted(video_qualities, reverse=True),
                'audio_qualities': sorted(audio_qualities, reverse=True)
            }
    except Exception:
        return {'video_qualities': [1080, 720, 480], 'audio_qualities': [320, 192, 128]}

def sanitize_filename(filename):
    """Sanitize filename for cross-platform compatibility."""
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    return filename[:200]  # Limit length

def download_content(url, start_index, end_index, output_dir, format_type, include_subtitles, quality='best', content_type='playlist'):
    """Enhanced download function for both videos and playlists."""
    
    # Expand and validate output directory
    output_dir = os.path.expanduser(output_dir)
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return False, f"Cannot create output directory: {str(e)}"

    # Build yt-dlp options with anti-bot detection measures
    ydl_opts = {
        'ignoreerrors': True,
        'no_warnings': False,
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
        # Anti-bot detection headers and settings
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        'cookiesfrombrowser': None,
        'sleep_interval': 2,  # Add delay between requests
        'max_sleep_interval': 10,
        'sleep_interval_subtitles': 2,
        # Use different extractors as fallback
        'extractor_args': {
            'youtube': {
                'skip': ['dash', 'hls'],
                'player_skip': ['configs'],
            }
        }
    }

    # Set playlist items only for playlists
    if content_type == 'playlist':
        ydl_opts['playlist_items'] = f'{start_index}-{end_index}' if start_index != end_index else str(start_index)

    # Format-specific options
    if format_type == 'Video (MP4)':
        if quality == 'best':
            ydl_opts['format'] = 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best'
        elif quality == 'medium':
            ydl_opts['format'] = 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best'
        else:  # low
            ydl_opts['format'] = 'bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]/best'
        
        if content_type == 'playlist':
            ydl_opts['outtmpl'] = os.path.join(output_dir, '%(playlist_index)s - %(title)s.%(ext)s')
        else:
            ydl_opts['outtmpl'] = os.path.join(output_dir, '%(title)s.%(ext)s')
    
    elif format_type == 'Audio (MP3)':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320' if quality == 'best' else ('192' if quality == 'medium' else '128'),
        }]
        if content_type == 'playlist':
            ydl_opts['outtmpl'] = os.path.join(output_dir, '%(playlist_index)s - %(title)s.%(ext)s')
        else:
            ydl_opts['outtmpl'] = os.path.join(output_dir, '%(title)s.%(ext)s')
    
    elif format_type == 'Audio (M4A)':
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
        if content_type == 'playlist':
            ydl_opts['outtmpl'] = os.path.join(output_dir, '%(playlist_index)s - %(title)s.%(ext)s')
        else:
            ydl_opts['outtmpl'] = os.path.join(output_dir, '%(title)s.%(ext)s')

    # Subtitle options
    if include_subtitles:
        ydl_opts['writesubtitles'] = True
        ydl_opts['writeautomaticsub'] = True
        ydl_opts['subtitleslangs'] = ['en', 'en-US', 'en-GB', 'auto']

    # Progress tracking
    downloaded_count = 0
    total_count = end_index - start_index + 1 if content_type == 'playlist' else 1
    
    def progress_hook(d):
        nonlocal downloaded_count
        
        if d['status'] == 'downloading':
            filename = d.get('filename', 'Unknown')
            filename = os.path.basename(filename)
            
            # Parse percentage
            percent_str = d.get('_percent_str', '0.0%')
            try:
                percent_val = float(percent_str.replace('%', '')) / 100
            except:
                percent_val = 0
            
            # Update session state
            st.session_state.current_file = filename
            st.session_state.current_progress = percent_val
            st.session_state.overall_progress = (downloaded_count + percent_val) / total_count
            st.session_state.download_speed = d.get('_speed_str', 'Unknown')
            st.session_state.eta = d.get('_eta_str', 'Unknown')
            
        elif d['status'] == 'finished':
            downloaded_count += 1
            st.session_state.overall_progress = downloaded_count / total_count
            st.session_state.downloaded_files.append(os.path.basename(d['filename']))

    ydl_opts['progress_hooks'] = [progress_hook]

    # Initialize session state for progress tracking
    if 'downloaded_files' not in st.session_state:
        st.session_state.downloaded_files = []
    if 'current_file' not in st.session_state:
        st.session_state.current_file = ""
    if 'current_progress' not in st.session_state:
        st.session_state.current_progress = 0
    if 'overall_progress' not in st.session_state:
        st.session_state.overall_progress = 0
    if 'download_speed' not in st.session_state:
        st.session_state.download_speed = ""
    if 'eta' not in st.session_state:
        st.session_state.eta = ""

    # Reset progress tracking
    st.session_state.downloaded_files = []
    st.session_state.current_file = ""
    st.session_state.current_progress = 0
    st.session_state.overall_progress = 0
    st.session_state.download_speed = ""
    st.session_state.eta = ""

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return True, f"Successfully downloaded {len(st.session_state.downloaded_files)} file(s) to {output_dir}"
    
    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            return False, "YouTube is currently blocking requests from this server due to bot detection. This is a common issue with cloud hosting. Please try again later or consider using the app locally."
        elif "Private video" in error_msg:
            return False, "Content is private or unavailable"
        elif "Video unavailable" in error_msg:
            return False, "Content is no longer available"
        elif "Sign in to confirm your age" in error_msg:
            return False, "Age-restricted content detected. Cannot download without authentication"
        elif "Requested format is not available" in error_msg:
            return False, "Requested quality/format is not available. Try a different quality setting"
        else:
            return False, f"Download error: {error_msg}"

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📺 YouTube Content Downloader</h1>
        <p>Download videos or audio from YouTube videos and playlists with ease</p>
    </div>
    """, unsafe_allow_html=True)

    # Important notice for cloud hosting
    st.info("""
    📋 **Important Notice**: This app is hosted on Streamlit Cloud. YouTube may occasionally block requests from cloud servers 
    due to bot detection. If you encounter issues, please try again later or consider running the app locally for best performance.
    """)

    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Format selection
        format_type = st.selectbox(
            "📁 Download Format",
            ["Video (MP4)", "Audio (MP3)", "Audio (M4A)"],
            help="Choose your preferred format"
        )
        
        # Quality selection
        quality = st.selectbox(
            "🎥 Quality",
            ["best", "medium", "low"],
            help="Higher quality = larger file size"
        )
        
        # Output directory
        output_dir = st.text_input(
            "📂 Output Directory",
            value="~/Downloads/YouTube",
            help="Where to save downloaded files"
        )
        
        include_subtitles = st.checkbox(
            "📝 Include Subtitles",
            value=False,
            help="Download subtitle files when available"
        )

        # Advanced options
        with st.expander("🔧 Advanced Options"):
            concurrent = st.checkbox(
                "Enable concurrent downloads",
                value=False,
                help="May speed up downloads but use more resources"
            )
            
            retry_attempts = st.number_input(
                "Retry attempts",
                min_value=1,
                max_value=5,
                value=3,
                help="Number of times to retry failed downloads"
            )

        # Help section
        with st.expander("❓ How to Use"):
            st.markdown("""
            **For Single Videos:**
            - Paste any YouTube video URL
            - Choose format and quality
            - Click download
            
            **For Playlists:**
            - Paste playlist URL
            - Set video range (optional)
            - Choose format and quality
            - Click download
            
            **Supported URLs:**
            - `youtube.com/watch?v=...` (single video)
            - `youtu.be/...` (single video)
            - `youtube.com/playlist?list=...` (playlist)
            - `youtube.com/watch?v=...&list=...` (playlist)
            """)

    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔗 Content URL")
        
        # URL input with validation
        content_url = st.text_input(
            "YouTube URL (Video or Playlist)",
            placeholder="https://www.youtube.com/watch?v=... or https://www.youtube.com/playlist?list=...",
            help="Paste any YouTube video or playlist URL"
        )
        
        content_info = None
        content_type = None
        
        # Real-time URL validation and info fetching
        if content_url:
            is_valid, message, url_type = validate_url(content_url)
            if is_valid:
                st.success(f"✅ {message}")
                content_type = url_type
                
                # Get content info with caching
                if 'cached_url' not in st.session_state or st.session_state.cached_url != content_url:
                    with st.spinner("Fetching content information..."):
                        content_info = get_content_info(content_url)
                        if content_info:
                            st.session_state.cached_info = content_info
                            st.session_state.cached_url = content_url
                        else:
                            # If content info fails, show a simplified interface
                            st.warning("⚠️ Unable to fetch content preview. You can still try to download the content.")
                            st.session_state.cached_info = {
                                'type': url_type,
                                'title': 'Content Preview Unavailable',
                                'uploader': 'Unknown',
                                'count': 1 if url_type == 'video' else 10,  # Default values
                                'description': '',
                                'duration': 0,
                                'view_count': 0,
                                'thumbnail': '',
                                'like_count': 0,
                                'tags': []
                            }
                            st.session_state.cached_url = content_url
                            content_info = st.session_state.cached_info
                else:
                    content_info = st.session_state.cached_info
                    
                if content_info:
                    # Display content preview
                    if content_info['type'] == 'playlist':
                        st.markdown(f"""
                        <div class="info-box">
                            <h3>📑 {content_info['title']}</h3>
                            <p><strong>👤 Channel:</strong> {content_info['uploader']}</p>
                            <p><strong>📊 Videos:</strong> {content_info['count']}</p>
                            <p><strong>⏱️ Total Duration:</strong> {format_duration(content_info.get('duration_total', 0))}</p>
                            <p><strong>👁️ Views:</strong> {format_number(content_info.get('view_count', 0))}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show preview of first few videos
                        if content_info.get('preview_videos'):
                            st.subheader("🎬 Preview Videos")
                            for i, video in enumerate(content_info['preview_videos'][:3], 1):
                                if video:
                                    st.markdown(f"**{i}.** {video.get('title', 'Unknown Title')} ({format_duration(video.get('duration', 0))})")
                    
                    else:  # Single video
                        col1a, col1b = st.columns([2, 1])
                        with col1a:
                            st.markdown(f"""
                            <div class="info-box">
                                <h3>🎥 {content_info['title']}</h3>
                                <p><strong>👤 Channel:</strong> {content_info['uploader']}</p>
                                <p><strong>⏱️ Duration:</strong> {format_duration(content_info.get('duration', 0))}</p>
                                <p><strong>👁️ Views:</strong> {format_number(content_info.get('view_count', 0))}</p>
                                <p><strong>👍 Likes:</strong> {format_number(content_info.get('like_count', 0))}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col1b:
                            if content_info.get('thumbnail'):
                                st.image(content_info['thumbnail'], caption="Video Thumbnail", use_container_width=True)
                        
                        # Show tags if available
                        if content_info.get('tags'):
                            st.markdown("**🏷️ Tags:** " + ", ".join(content_info['tags']))
            else:
                st.error(f"❌ {message}")

        # Download range (only for playlists)
        if content_type == 'playlist' and content_info:
            st.subheader("🎯 Download Range")
            col1a, col1b = st.columns(2)
            with col1a:
                start_index = st.number_input(
                    "Start Video Index",
                    min_value=1,
                    max_value=content_info['count'],
                    value=1,
                    step=1,
                    help="First video to download (1 = first video in playlist)"
                )
            with col1b:
                end_index = st.number_input(
                    "End Video Index",
                    min_value=start_index,
                    max_value=content_info['count'],
                    value=min(5, content_info['count']),
                    step=1,
                    help="Last video to download"
                )
        else:
            start_index = 1
            end_index = 1

    with col2:
        st.subheader("📊 Download Status")
        
        # Progress indicators with enhanced info
        if 'overall_progress' in st.session_state and st.session_state.overall_progress > 0:
            st.progress(st.session_state.overall_progress, text="Overall Progress")
            
        if 'current_progress' in st.session_state and st.session_state.current_file:
            st.progress(st.session_state.current_progress, text="Current File")
            st.caption(f"📂 {st.session_state.current_file}")
            
            # Show download speed and ETA
            if st.session_state.get('download_speed'):
                st.caption(f"⚡ Speed: {st.session_state.download_speed}")
            if st.session_state.get('eta'):
                st.caption(f"⏰ ETA: {st.session_state.eta}")

        # Downloaded files list
        if 'downloaded_files' in st.session_state and st.session_state.downloaded_files:
            st.subheader("✅ Downloaded Files")
            for file in st.session_state.downloaded_files[-5:]:  # Show last 5
                st.text(f"📄 {file}")

    # Download button and validation
    st.markdown("---")
    
    # Validation before download
    can_download = True
    error_messages = []
    
    if not content_url:
        error_messages.append("Please enter a YouTube URL")
        can_download = False
    elif not validate_url(content_url)[0]:
        error_messages.append("Invalid YouTube URL")
        can_download = False
    
    if content_type == 'playlist' and start_index > end_index:
        error_messages.append("Start index must be ≤ end index")
        can_download = False
    
    if not output_dir.strip():
        error_messages.append("Please specify output directory")
        can_download = False

    if error_messages:
        for msg in error_messages:
            st.error(f"❌ {msg}")

    # Download button with dynamic text
    download_text = "🚀 Download Video" if content_type == 'video' else "🚀 Download Playlist"
    if content_type == 'playlist' and content_info:
        download_count = end_index - start_index + 1
        download_text += f" ({download_count} video{'s' if download_count > 1 else ''})"
    
    if st.button(download_text, disabled=not can_download, use_container_width=True):
        if can_download:
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            with status_placeholder:
                st.info("🔄 Initializing download...")
            
            success, message = download_content(
                content_url, start_index, end_index, output_dir, 
                format_type, include_subtitles, quality, content_type
            )
            
            status_placeholder.empty()
            
            if success:
                st.balloons()
                st.success(f"🎉 {message}")
                
                # Show download summary
                if st.session_state.downloaded_files:
                    with st.expander("📋 Download Summary", expanded=True):
                        st.write(f"**Total files downloaded:** {len(st.session_state.downloaded_files)}")
                        st.write(f"**Format:** {format_type}")
                        st.write(f"**Quality:** {quality}")
                        st.write(f"**Saved to:** `{output_dir}`")
                        st.write("**Files:**")
                        for file in st.session_state.downloaded_files:
                            st.text(f"  • {file}")
            else:
                st.error(f"💥 {message}")
                st.info("💡 **Troubleshooting Tips:**\n"
                       "- **Bot Detection**: YouTube may block cloud servers - try again later\n"
                       "- **Run Locally**: Download the app from GitHub for best reliability\n"
                       "- **Check Content**: Ensure the content is public and available\n"
                       "- **Internet Connection**: Verify your connection is stable\n"
                       "- **Output Directory**: Check write permissions to the directory\n"
                       "- **Quality Settings**: Try a different quality setting\n"
                       "- **Geo-blocking**: Some content might be region-restricted")

                # Add GitHub link for local installation
                st.markdown("""
                🔗 **For best performance, run locally:**
                ```bash
                git clone https://github.com/dhecaptain/youtube-downloader-app.git
                cd youtube-downloader-app
                pip install -r requirements.txt
                streamlit run app.py
                ```
                """)

    # Quick actions for common use cases
    if content_info:
        st.markdown("---")
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📱 Mobile Quality (480p)", use_container_width=True):
                st.session_state.quick_download = {
                    'format': 'Video (MP4)',
                    'quality': 'low'
                }
        
        with col2:
            if st.button("🎵 Audio Only (MP3)", use_container_width=True):
                st.session_state.quick_download = {
                    'format': 'Audio (MP3)',
                    'quality': 'best'
                }
        
        with col3:
            if st.button("🎬 Best Quality", use_container_width=True):
                st.session_state.quick_download = {
                    'format': 'Video (MP4)',
                    'quality': 'best'
                }

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <small>
        🔒 This tool respects YouTube's terms of service. Use responsibly.<br>
        ⚡ Powered by yt-dlp • Made with ❤️ using Streamlit<br>
        📱 Supports both individual videos and playlists
        </small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()