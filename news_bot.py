import os
import feedparser
from linebot import LineBotApi
from linebot.models import TextSendMessage
from datetime import datetime

# =================設定區=================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')

# 最新版關鍵字清單：包含財經、AI、心理學、材料科學
KEYWORDS = [
    "財經 趨勢",              # 1. 財經
    "AI 人工智慧 生成式",      # 2. AI
    "心理學 最新研究",         # 3. 心理學新知
    "材料科學 新技術",         # 4. 材料科技應用
    "材料科學 研究突破"        # 5. 材料學術研究
]
# =======================================

def get_google_news(query):
    """抓取 Google News RSS 並回傳前 3 則"""
    # 將空格替換為 + 號以符合 URL 格式
    encoded_query = query.replace(' ', '+')
    # 使用繁體中文 (zh-TW) 和台灣地區 (TW) 的設定
    rss_url = f'https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
    
    feed = feedparser.parse(rss_url)
    news_list = []
    
    # 只取前 3 則最新新聞
    for entry in feed.entries[:3]:
        news_list.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published
        })
    return news_list

def format_message(news_data):
    """將新聞整理成易讀的 LINE 訊息格式"""
    today = datetime.now().strftime('%Y/%m/%d')
    message = f"🤖 {today} 每日多元知識早報\n"
    
    for category, items in news_data.items():
        # 標題裝飾：只顯示關鍵字的第一部分
        clean_category = category.split(' ')[0] 
        message += f"\n📌【{clean_category}】\n"
        
        if not items:
            message += "無最新相關新聞\n"
        
        for idx, item in enumerate(items, 1):
            # 移除標題後面的媒體名稱 (例如 " - Yahoo新聞")
            clean_title = item['title'].split(' - ')[0]
            message += f"{idx}. {clean_title}\n"
            message += f"🔗 {item['link']}\n"
            
    message += "\n------------------\n知識就是力量 💪"
    return message.strip()

def main():
    # 安全檢查
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("錯誤：未設定環境變數 (LINE Token 或 User ID)")
        return

    # 1. 初始化 LINE Bot
    try:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    except Exception as e:
        print(f"LINE Bot 初始化失敗: {e}")
        return

    # 2. 抓取所有關鍵字的新聞
    all_news = {}
    print("開始抓取新聞...")
    for keyword in KEYWORDS:
        print(f"正在搜尋: {keyword}")
        try:
            news_items = get_google_news(keyword)
            all_news[keyword] = news_items
        except Exception as e:
            print(f"抓取 {keyword} 時發生錯誤: {e}")
            all_news[keyword] = []

    # 3. 整理訊息
    text_content = format_message(all_news)

    # 4. 發送訊息
    try:
        # LINE 文字訊息上限截斷
        if len(text_content) > 2000:
            text_content = text_content[:1990] + "\n...(內容過長已截斷)"
            
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text_content))
        print("訊息發送成功！")
    except Exception as e:
        print(f"訊息發送失敗: {e}")

if __name__ == "__main__":
    main()