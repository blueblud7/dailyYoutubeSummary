#!/usr/bin/env python3
"""
YouTube URL 추출 기능 테스트
"""

import re

class YouTubeURLTester:
    def __init__(self):
        # YouTube URL 패턴 정의
        self.youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'https?://youtu\.be/([a-zA-Z0-9_-]+)',
            r'https?://(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]+)',
            r'https?://(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)'
        ]
        
    def extract_video_id(self, url: str) -> str:
        """YouTube URL에서 영상 ID 추출"""
        # @ 기호나 기타 문자가 앞에 붙은 경우 제거
        clean_url = url.strip()
        
        # @ 기호로 시작하는 경우 제거
        if clean_url.startswith('@'):
            clean_url = clean_url[1:]
        
        # 공백이나 기타 문자 제거
        clean_url = clean_url.strip()
        
        for pattern in self.youtube_patterns:
            match = re.search(pattern, clean_url)
            if match:
                # URL 파라미터에서 video ID만 추출 (? 이후 제거)
                video_id = match.group(1)
                if '&' in video_id:
                    video_id = video_id.split('&')[0]
                if '?' in video_id:
                    video_id = video_id.split('?')[0]
                return video_id
        return None

def test_url_extraction():
    """URL 추출 기능 테스트"""
    
    tester = YouTubeURLTester()
    
    # 테스트할 URL들
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ&list=PLxyz",
        "https://youtu.be/dQw4w9WgXcQ?t=30",
        "@https://youtu.be/hWqWQIIOtHM?si=PVnHhifSm8MfwBZA",  # @ 기호가 포함된 URL
        "@https://www.youtube.com/watch?v=hWqWQIIOtHM&si=xyz",  # @ 기호와 파라미터가 포함된 URL
        " @https://youtu.be/hWqWQIIOtHM ",  # 앞뒤 공백과 @ 기호
        "이것은 YouTube URL이 아닙니다",
        "https://other-site.com/video"
    ]
    
    print("🔍 YouTube URL 추출 테스트 (개선된 버전)\n")
    
    for i, url in enumerate(test_urls, 1):
        video_id = tester.extract_video_id(url)
        
        print(f"{i:2d}. {url}")
        if video_id:
            print(f"    ✅ 영상 ID: {video_id}")
        else:
            print(f"    ❌ 영상 ID를 찾을 수 없음")
        print()

if __name__ == "__main__":
    test_url_extraction() 