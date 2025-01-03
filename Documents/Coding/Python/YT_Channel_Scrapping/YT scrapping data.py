from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta

api_keys = [
    'AIzaSyAluTiYkhogGhHsnBF9lLxSKDiPwUod8cg'
]

def get_youtube_service():
    for api_key in api_keys:
        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            # Coba melakukan request untuk memverifikasi API key
            youtube.search().list(q="test", part="id", maxResults=1).execute()
            print(f"Using API key: {api_key}")  # Debug log
            return youtube
        except HttpError as e:
            print(f"API key {api_key} failed: {e}")  # Debug log
            continue
    raise Exception("All API keys failed")

# Mendapatkan service youtube
youtube = get_youtube_service()

# Fungsi untuk mencari channel berdasarkan keyword dengan paginasi
def search_channels(keyword, max_results=None):
    channels = []
    request = youtube.search().list(
        q=keyword,
        type='channel',
        part='snippet',
        maxResults=50
    )
    
    while request:
        response = request.execute()
        channels.extend(response['items'])
        
        request = youtube.search().list_next(request, response)
        
        if max_results and len(channels) >= max_results:
            break
    
    print(f"Total channels found for keyword '{keyword}': {len(channels)}")  # Debug log
    return channels

# Fungsi untuk mendapatkan detail channel
def get_channel_details(channel_id):
    request = youtube.channels().list(
        part='snippet,statistics,contentDetails',
        id=channel_id
    )
    response = request.execute()
    return response['items'][0]

# Fungsi untuk mendapatkan video terakhir dari channel
def get_last_video_date(channel_id):
    request = youtube.search().list(
        channelId=channel_id,
        part='snippet',
        order='date',
        maxResults=1
    )
    response = request.execute()
    if response['items']:
        last_video_date = response['items'][0]['snippet']['publishedAt']
        return datetime.strptime(last_video_date, '%Y-%m-%dT%H:%M:%SZ')
    return None

# Fungsi utama untuk mencari channel yang sesuai kriteria dan menyimpan hasil ke dalam file
def find_channels(keyword, min_subs=4000, max_subs=20000, days_since_last_video=30, max_results=None):
    channels = search_channels(keyword, max_results=max_results)
    result = []

    # Baca file channels.txt untuk mendapatkan daftar channel yang sudah ada
    try:
        with open('channels.txt', 'r') as file:
            existing_channels = file.read().splitlines()
    except FileNotFoundError:
        existing_channels = []

    for channel in channels:
        channel_id = channel['id']['channelId']
        
        # Periksa apakah channel sudah ada dalam file channels.txt
        if f"https://www.youtube.com/channel/{channel_id}" in existing_channels:
            print(f"Channel already exists: {channel_id}")
            continue

        details = get_channel_details(channel_id)
        
        # Memeriksa negara channel
        country = details['snippet'].get('country', '')
        if country not in ['US', 'CA', 'GB']:
            continue
        
        subs_count = int(details['statistics']['subscriberCount'])
        if min_subs <= subs_count <= max_subs:
            last_video_date = get_last_video_date(channel_id)
            if last_video_date and (datetime.now() - last_video_date).days <= days_since_last_video:
                result.append({
                    'channel_id': channel_id,
                    'title': details['snippet']['title'],
                    'subscribers': subs_count,
                    'last_video_date': last_video_date.strftime('%Y-%m-%d'),
                    'country': country
                })
    
    print(f"Total channels meeting criteria for keyword '{keyword}': {len(result)}")  # Debug log

    # Simpan hasil ke dalam file
    with open('channels.txt', 'a') as file:  # Append mode
        for channel in result:
            channel_link = f"https://www.youtube.com/channel/{channel['channel_id']}"
            file.write(f"{channel_link}\n")
    
    return result

# Membaca keyword dari keyword.txt
def read_keywords_from_file(filename):
    with open(filename, 'r') as file:
        keywords = file.read().splitlines()
    return keywords

# Fungsi utama untuk menjalankan proses scraping berdasarkan keyword dari file
def main():
    keywords = read_keywords_from_file('keyword.txt')
    for keyword in keywords:
        find_channels(keyword)

# Menjalankan fungsi utama
if __name__ == "__main__":
    main()
