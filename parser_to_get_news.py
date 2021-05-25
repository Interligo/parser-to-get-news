import time

import requests
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup as bs


class NewsCrawler:
    def __init__(self) -> None:
        self.browser = webdriver.Chrome()
        self.session = requests.Session()
        self.headers = {
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/88.0.4324.190 Safari/537.36'
        }
        self.news_url = 'https://xn--90adear.xn--p1ai/r/65/news/'
        self.root_news_url = 'https://xn--90adear.xn--p1ai/'
        self.pages_count = 0
        self.links_to_parse = []
        self.result_file_name = 'news_65_region.xlsx'

        self.news_dates = []
        self.news_titles = []
        self.news_texts = []

    def get_data_from_page(self, link: str) -> str:
        self.browser.get(link)
        time.sleep(5)
        html_source = self.browser.page_source
        return html_source

    def find_news_page_count(self, html: str) -> None:
        found_pages_numbers = []
        for element in html:
            found_data = element.find('a').text
            try:
                found_data = int(found_data)
                found_pages_numbers.append(found_data)
            except ValueError:
                pass
        self.pages_count = max(found_pages_numbers)

    def parse_page_to_get_links(self, data: str) -> None:
        html = bs(data, 'lxml')
        all_news_divs = html.find_all('div', {'class': 'sl-item-title'})
        for div in all_news_divs:
            link = div.find('a', href=True)
            self.links_to_parse.append(link['href'])

    def save_data_to_xlsx(self, date: list, title: list, text: list) -> None:
        df = pd.DataFrame()
        df['Дата публикации'] = date
        df['Заголовок'] = title
        df['Текст'] = text

        with pd.ExcelWriter(self.result_file_name, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, sheet_name='ГИБДД')
            writer.save()

    def grab_page_data(self, link: str) -> None:
        raw_text, text = [], []

        data = self.get_data_from_page(link)

        html = bs(data, 'lxml')
        self.news_dates.append(html.find('div', {'class': 'news-date'}).text)
        self.news_titles.append(html.find('h2').text)
        all_news_text = html.find_all('div', {'class': 'article-text'})
        for paragraph in all_news_text[0].find_all('p'):
            raw_text.append(paragraph.text)
        self.news_texts.append([' '.join(raw_text)])

    def parse_news_links(self):
        while self.links_to_parse:
            current_link = self.links_to_parse.pop()
            full_link = self.root_news_url + current_link
            self.grab_page_data(full_link)

    def parse(self) -> None:
        html_source = self.get_data_from_page(self.news_url)

        html = bs(html_source, 'lxml')
        pagination_data = html.find('ul', class_='paginator')

        self.find_news_page_count(pagination_data)

        for page_number in range(1, int(self.pages_count)+1):
            page_to_parse = self.browser.find_element_by_link_text(str(page_number))
            page_to_parse.click()
            time.sleep(5)

            data_from_page = self.browser.page_source
            self.parse_page_to_get_links(data_from_page)

        self.parse_news_links()
        self.browser.quit()
        self.save_data_to_xlsx(date=self.news_dates, title=self.news_titles, text=self.news_texts)
