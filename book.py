import io
import re

import requests

from bs4 import BeautifulSoup


chinese_char = re.compile(r"[\u4e00-\u9fa5]")

def get_html(link: str) -> BeautifulSoup | None:
    try:
        # 發送 GET 請求取得網頁內容
        response = requests.get(link)
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.text, "html.parser")
        return soup
    except Exception:
        return None

class Czbooks():
    def __init__(self, link: str) -> None:
        soup = get_html(link)
        detail_div = soup.find("div", class_="novel-detail")

        self.link = link
        self.title = detail_div.find("span", class_="title").text
        self.author = (
            "作者: " + detail_div.find("span", class_="author").contents[1].text
        )
        self.description = detail_div.find("div", class_="description").text
        # hashtag
        hashtag = soup.find("ul", class_="hashtag")
        self.hashtags = hashtag.find_all("li", class_="item")
        # 章節列表
        ul_list = soup.find("ul", id="chapter-list")
        links = ul_list.find_all("a")
        # 計算章節數
        self.ch_count = len(links)
        self.ch_list = links

    def hashtag(self):
        return ", ".join(tag.text for tag in self.hashtags)


    def get_content(self):
        self.content = ""
        self.content += f"書本連結: {self.link}\n標籤: {self.hashtag()}"
        # 逐章爬取內容
        for index, link in enumerate(self.ch_list, start=1):
            process = round(index*100/self.ch_count, 2)
            print(
                f"\r進度: {index}/{self.ch_count} {process}%",
                end=""
            )
            soup = get_html("https:"+link["href"])
            # 尋找章節名稱
            # 尋找章節名稱 div 標籤
            ch_name = soup.find("div", class_="name")
            # 尋找內文 div 標籤
            div_content = ch_name.find_next("div", class_="content")
            # 儲存找到的內容
            self.content += f"\n\n{'='*32} {ch_name.text} {'='*32}\n\n"
            self.content += div_content.text.strip()
        self.words_count = len(re.findall(chinese_char, self.content))


book_url = input("請輸入網站連結: ")
book = Czbooks(book_url)
book.get_content()
print(book.words_count)
with open(f"{book.title}.txt", "w", encoding="utf-8") as file:
    file.write(book.content)
