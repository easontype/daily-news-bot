import os
import feedparser
import requests
import json
from linebot import LineBotApi
from linebot.models import FlexSendMessage
from datetime import datetime
import time

# =================設定區=================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
# GitHub Pages 的網址 (請將 [您的帳號] 和 [倉庫名] 換成您的)
# 例如: https://john-doe.github.io/daily-news-bot/
# 注意：程式會自動嘗試偵測，但建議您稍後在 GitHub Secret 設定 WEBSITE_URL 會更準確
WEBSITE_URL = os.environ.get('WEBSITE_URL') 

KEYWORDS = [
    "財經 趨勢",
    "AI 人工智慧 生成式",
    "心理學 最新研究",
    "材料科學 新技術",
    "材料科學 研究突破"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
# =======================================

def get_original_url(google_url):
    """解析 Google News 轉址"""
    try:
        response = requests.get(google_url, headers=HEADERS, allow_redirects=True, timeout=5)
        return response.url
    except:
        return google_url

def get_google_news(query):
    """抓取並解析新聞"""
    encoded_query = query.replace(' ', '+')
    rss_url = f'https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
    feed = feedparser.parse(rss_url)
    news_list = []
    
    for entry in feed.entries[:3]: # 取前3則
        time.sleep(0.2) # 稍微加速，僅休眠0.2秒
        real_link = get_original_url(entry.link)
        news_list.append({
            'title': entry.title.split(' - ')[0],
            'link': real_link,
            'source': entry.source.title if hasattr(entry, 'source') else 'Google News',
            'date': entry.published
        })
    return news_list

def generate_html(all_news):
    """生成漂亮的 HTML 網頁"""
    today_str = datetime.now().strftime('%Y年%m月%d日')
    
    # HTML 頭部與 CSS (使用 Tailwind CSS CDN)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{today_str} 每日知識早報</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
            body {{ font-family: 'Noto Sans TC', sans-serif; }}
        </style>
    </head>
    <body class="bg-gray-50 text-gray-800 pb-10">
        <header class="bg-indigo-600 text-white p-6 shadow-lg">
            <div class="max-w-3xl mx-auto text-center">
                <h1 class="text-2xl font-bold tracking-wider">每日多元知識早報</h1>
                <p class="mt-2 text-indigo-200 text-sm">📅 {today_str} • 財經 / AI / 心理學 / 材料科學</p>
            </div>
        </header>

        <main class="max-w-3xl mx-auto p-4 space-y-8 mt-4">
    """
    
    # 生成新聞卡片
    for category, items in all_news.items():
        cat_name = category.split(' ')[0]
        color_class = "border-indigo-500"
        if "財經" in category: color_class = "border-emerald-500"
        elif "AI" in category: color_class = "border-blue-500"
        elif "心理" in category: color_class = "border-pink-500"
        elif "材料" in category: color_class = "border-amber-500"

        html_content += f"""
            <section class="bg-white rounded-xl shadow-sm border-l-4 {color_class} overflow-hidden">
                <div class="bg-gray-50 px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                    <h2 class="font-bold text-lg text-gray-700">{cat_name}</h2>
                    <span class="text-xs text-gray-400 bg-white px-2 py-1 rounded border">News</span>
                </div>
                <div class="divide-y divide-gray-100">
        """
        
        if not items:
            html_content += '<div class="p-4 text-gray-400 text-center text-sm">今日無相關重大新聞</div>'
        
        for item in items:
            html_content += f"""
                <a href="{item['link']}" target="_blank" class="block p-4 hover:bg-gray-50 transition-colors group">
                    <h3 class="font-medium text-gray-800 group-hover:text-indigo-600 leading-relaxed">{item['title']}</h3>
                    <div class="mt-2 flex items-center text-xs text-gray-400 space-x-2">
                        <span class="bg-gray-100 px-2 py-0.5 rounded text-gray-500">{item['source']}</span>
                        <span>點擊閱讀全文 &rarr;</span>
                    </div>
                </a>
            """
        
        html_content += """
                </div>
            </section>
        """

    # HTML 尾部
    html_content += """
            <div class="text-center text-gray-400 text-xs mt-8">
                <p>資料來源：Google News RSS</p>
                <p>Designed for Automated Learning</p>
            </div>
        </main>
    </body>
    </html>
    """
    
    # 寫入 index.html 檔案
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("網頁生成完畢: index.html")

def send_flex_message(line_bot_api, user_id, url):
    """發送精美的 Flex Message"""
    today = datetime.now().strftime('%m/%d')
    
    # 如果網址是 None (尚未設定)，給一個預設提示
    target_url = url if url else "https://github.com"
    
    flex_json = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1080&auto=format&fit=crop",
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
            "action": { "type": "uri", "uri": target_url }
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{today} 每日早報",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#1F2937"
                },
                {
                    "type": "text",
                    "text": "財經 • AI • 心理學 • 材料科學",
                    "size": "xs",
                    "color": "#6B7280",
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {"type": "text", "text": "✅ 最新市場財經趨勢", "size": "sm", "color": "#4B5563"},
                        {"type": "text", "text": "✅ 生成式 AI 技術新知", "size": "sm", "color": "#4B5563"},
                        {"type": "text", "text": "✅ 心理學與材料研究", "size": "sm", "color": "#4B5563"}
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "color": "#4F46E5",
                    "action": {
                        "type": "uri",
                        "label": "立即閱讀今日新聞",
                        "uri": target_url
                    }
                }
            ]
        }
    }

    try:
        line_bot_api.push_message(user_id, FlexSendMessage(alt_text=f"{today} 新聞早報已送達", contents=flex_json))
        print("Flex Message 發送成功")
    except Exception as e:
        print(f"發送失敗: {e}")

def main():
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("錯誤：未設定 LINE 環境變數")
        return

    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

    # 1. 抓新聞
    all_news = {}
    for keyword in KEYWORDS:
        print(f"搜尋: {keyword}")
        try:
            all_news[keyword] = get_google_news(keyword)
        except Exception as e:
            print(f"Error {keyword}: {e}")
            all_news[keyword] = []

    # 2. 生成 HTML 網頁檔案
    generate_html(all_news)
    
    # 3. 發送 LINE 連結
    # 如果 WEBSITE_URL 沒設定，試著組裝 GitHub Pages 預設網址
    final_url = WEBSITE_URL
    if not final_url:
        # 嘗試從環境變數抓 GitHub 資訊來組網址 (格式: https://user.github.io/repo)
        repo = os.environ.get('GITHUB_REPOSITORY') # 格式: username/repo
        if repo:
            username, reponame = repo.split('/')
            final_url = f"https://{username}.github.io/{reponame}/"
        else:
            final_url = "https://github.com" # 備用
            
    print(f"目標網址: {final_url}")
    send_flex_message(line_bot_api, LINE_USER_ID, final_url)

if __name__ == "__main__":
    main()
