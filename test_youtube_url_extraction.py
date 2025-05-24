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
        for pattern in self.youtube_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
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
        "이것은 YouTube URL이 아닙니다",
        "https://other-site.com/video"
    ]
    
    print("🔍 YouTube URL 추출 테스트\n")
    
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