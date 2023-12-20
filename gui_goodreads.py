import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import os
import requests
from urllib.parse import urljoin

class GoodreadsScraperGUI:
    def __init__(self, master):
        self.master = master
        master.title("Goodreads Webscraper GUI")

        # Maximize the window
        master.state("zoomed")

        # Center the widgets
        master.columnconfigure(0, weight=1)
        master.columnconfigure(1, weight=1)
        master.rowconfigure(0, weight=1)
        master.rowconfigure(1, weight=1)
        master.rowconfigure(2, weight=1)
        master.rowconfigure(3, weight=1)

        self.label_author = tk.Label(master, text="Author:")
        self.label_book_title = tk.Label(master, text="Book Title:")

        self.entry_author = tk.Entry(master)
        self.entry_book_title = tk.Entry(master)

        self.btn_search = tk.Button(master, text="Search Goodreads", command=self.search_goodreads)
        self.btn_download_cover = tk.Button(master, text="Download Book Cover", command=self.download_book_cover_btn, state=tk.DISABLED)
        self.btn_new_search = tk.Button(master, text="New Search", command=self.new_search)

        # Create Treeview widget
        self.tree = ttk.Treeview(master, columns=("Attribute", "Value"), show="headings", height=5)
        self.tree.heading("Attribute", text="Attribute")
        self.tree.heading("Value", text="Value")

        # Create Text widget for displaying summary
        self.summary_text = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=50, height=10, state=tk.DISABLED)

        self.label_author.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.label_book_title.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.entry_author.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.entry_book_title.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.btn_search.grid(row=2, column=0, pady=10)
        self.btn_download_cover.grid(row=2, column=1, pady=10)
        self.tree.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.summary_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Configure weights for resizing
        for i in range(5):
            master.rowconfigure(i, weight=1)
            master.columnconfigure(i, weight=1)

        self.current_search_folder = None
        self.first_page_soup = None

    def search_goodreads(self):
        author = self.entry_author.get()
        book_title = self.entry_book_title.get()

        if not author or not book_title:
            messagebox.showerror("Error", "Please enter both author and book title.")
            return

        search_query = f"{book_title} by {author}"
        results = self.run_webscraper(search_query)

        # Create a folder for the current search
        search_folder = os.path.join(os.getcwd(), search_query.replace(" ", "_"))
        os.makedirs(search_folder, exist_ok=True)
        self.current_search_folder = search_folder

        # Enable the download button
        self.btn_download_cover.config(state=tk.NORMAL)

        # Clear existing items in the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Display the results in the treeview
        for attribute, value in results.items():
            self.tree.insert("", tk.END, values=(attribute, value))

        # Display the summary in the summary_text widget
        summary_value = results.get("Summary", "")
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary_value)
        self.summary_text.config(state=tk.DISABLED)

    def run_webscraper(self, search_query):
        base_url = "https://www.goodreads.com"
        driver = webdriver.Firefox()
        driver.maximize_window()

        try:
            search_href = "/search"
            full_url = urljoin(base_url, search_href)
            driver.get(full_url)

            search_box = driver.find_element("id", "search_query_main")
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)

            time.sleep(5)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            search_results = soup.find_all('a', class_='bookTitle')
            first_book_in_list = search_results[0]
            time.sleep(1)

            first_book_href = first_book_in_list.get('href')
            first_book_url = urljoin(base_url, first_book_href)
            driver.get(first_book_url)

            first_page_source = driver.page_source
            self.first_page_soup = BeautifulSoup(first_page_source, 'html.parser')

            star_rating, ratings_count, reviews_count = self.collect_rating_and_reviews(self.first_page_soup)
            page_count, publish_date = self.collect_page_and_publish_date(self.first_page_soup)
            summary = self.collect_summary(self.first_page_soup)
            genre_list = self.collect_genres(self.first_page_soup)
            kindle_or_cost = self.kindle_unlimited_or_not(self.first_page_soup)
            bookcover_url = self.download_book_cover(self.first_page_soup)

            return {
                "Star Rating": star_rating,
                "Total Ratings": ratings_count,
                "Total Reviews": reviews_count,
                "Page Count": page_count,
                "Publish Date": publish_date,
                "Summary": summary,
                "Genre List": genre_list,
                "Kindle or Cost": kindle_or_cost
            }

        finally:
            driver.quit()

    def collect_rating_and_reviews(self, soup):
        star_rating = soup.find_all('div', {'class': "RatingStatistics__rating"})
        star_rating_text = star_rating[0].get_text()
        final_star_rating_text = str(star_rating_text) + " average rating out of 5 stars"

        ratings_count = soup.find_all('span', {'data-testid': "ratingsCount"})
        ratings_count_text = ratings_count[0].get_text()

        reviews_count = soup.find_all('span', {'data-testid': "reviewsCount"})
        reviews_count_text = reviews_count[0].get_text()

        return final_star_rating_text, ratings_count_text, reviews_count_text

    def collect_page_and_publish_date(self, soup):
        page_count = soup.find_all('p', {'data-testid': "pagesFormat"})
        page_count_text = page_count[0].get_text()

        publish_date = soup.find_all('p', {'data-testid': "publicationInfo"})
        publish_date_text = publish_date[0].get_text()

        return page_count_text, publish_date_text

    def collect_summary(self, soup):
        summary = soup.find_all('div', {'data-testid': "description"})
        summary_text = summary[0].get_text()
        summary_text = summary_text[:-len("Show more")]

        return summary_text

    def collect_genres(self, soup):
        genre_list = []
        genres = soup.find_all('span', {'class': "BookPageMetadataSection__genreButton"})

        for genre in genres:
            genre_name = genre.get_text()
            genre_list.append(genre_name)

        return genre_list

    def kindle_unlimited_or_not(self, soup):
        cost = soup.find_all('button', {'class': "Button Button--buy Button--medium Button--block"})
        cost_text = cost[0].get_text()

        if 'Kindle Unlimited' in cost_text:
            display_cost_text = 'Book is on Kindle Unlimited'
            return display_cost_text
        else:
            cost_text = cost_text[len("Kindle"):]
            display_cost_text = 'Book is not on Kindle Unlimited. Cost is: ' + cost_text
            return display_cost_text

    def download_book_cover(self, soup):
        book_cover = soup.find_all('div', {'class': "BookCover__image"})
        book_cover_src = book_cover[0].find('img', attrs={'role': 'presentation'})
        book_cover_url = book_cover_src['src']

        response = requests.get(book_cover_url)

        if self.current_search_folder:
            # Save the book cover in the appropriate folder
            file_path = os.path.join(self.current_search_folder, "book_cover.jpg")

            with open(file_path, 'wb') as f:
                f.write(response.content)

            return file_path
        else:
            return None

    def download_book_cover_btn(self):
        if self.first_page_soup:
            file_path = self.download_book_cover(self.first_page_soup)

            if file_path:
                messagebox.showinfo("Download Complete", f"Book cover downloaded successfully.\nSaved at: {file_path}")
            else:
                messagebox.showerror("Error", "Book cover URL not found.")
        else:
            messagebox.showerror("Error", "Please perform a search first.")

    def new_search(self):
        # Reset the entries and result text
        self.entry_author.delete(0, tk.END)
        self.entry_book_title.delete(0, tk.END)
        self.current_search_folder = None
        self.first_page_soup = None

if __name__ == "__main__":
    root = tk.Tk()
    app = GoodreadsScraperGUI(root)
    root.mainloop()
