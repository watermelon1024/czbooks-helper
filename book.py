import io

import requests

from bs4 import BeautifulSoup


class crawler():
    def __init__(self, link: str = None) -> None:
        soup = self.get_html(link)
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

    def get_html(self, link: str) -> BeautifulSoup | None:
        try:
            # 發送 GET 請求取得網頁內容
            response = requests.get(link)
            if response.status_code != 200:
                return None
            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(response.text, "html.parser")
            return soup
        except Exception:
            return None

    def get_content(self):
        self.content = io.StringIO()
        self.content.writelines(f"書本連結: {self.link}\n標籤: {self.hashtag()}")
        # 逐章爬取內容
        for index, link in enumerate(self.ch_list, start=1):
            process = round(index*100/self.ch_count, 2)
            print(
                f"\r進度: {index}/{self.ch_count} {process}%",
                end=""
            )
            soup = self.get_html("https:"+link["href"])
            # 尋找章節名稱
            # 尋找章節名稱 div 標籤
            ch_name = soup.find("div", class_="name")
            # 尋找內文 div 標籤
            div_content = ch_name.find_next("div", class_="content")
            # 儲存找到的內容
            self.content.writelines(
                f"\n\n{'='*32} {ch_name.text} {'='*32}\n\n")
            self.content.writelines(div_content.text.strip())


book_url = input("請輸入網站連結: ")
book = crawler(book_url)
book.get_content()
with open(f"{book.title}.txt", "w", encoding="utf-8") as file:
    file.write(book.content.getvalue())
