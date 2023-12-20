from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import os

base_url = "https://www.goodreads.com"

def search_goodreads(query):

    # Global instantiation of Webdriver for Firefox
    driver = webdriver.Firefox()
    driver.maximize_window()
    
    try:
        search_href = "/search"
        full_url = urljoin(base_url, search_href)
        # Open Goodreads on search page
        driver.get(full_url)

        # Locate the search bar and input the query
        search_box = driver.find_element("id", "search_query_main")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        # Wait for the results to load (you may need to adjust the waiting time)
        time.sleep(5)
        
        # Get the HTML source after the search
        page_source = driver.page_source

        # Use BeautifulSoup to parse the HTML
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract and print information (you can modify this part based on your needs)
        search_results = soup.find_all('a', class_='bookTitle')
        
        first_book_in_list = search_results[0]
        time.sleep(1)
        
        # Open first book URL
        first_book_href = first_book_in_list.get('href')
        first_book_url = urljoin(base_url, first_book_href)
        driver.get(first_book_url)
        
        # Get the HTML source for the book HTML
        first_page_source = driver.page_source
        
        # Use BeautifulSoup to parse the HTML
        first_page_soup = BeautifulSoup(first_page_source, 'html.parser')
        
        ##################################################
        # PRINTS ALL PAGE CONTENTS IN HTML TO PAGE #
        #with open('soup.html', 'w', encoding="utf-8") as f:
        #    x = str(first_page_soup)
        #    f.write(x)
        ##################################################
        
        # Collect Rating stars and number of reviews
        star_rating, ratings_count, reviews_count = collect_rating_and_reviews(first_page_soup)
        
        # Collect number of pages and date published
        page_count, publish_date = collect_page_and_publish_date(first_page_soup)
        
        # Collect summary
        summary = collect_summary(first_page_soup)
        
        # Collect genres
        genre_list = collect_genres(first_page_soup)
        
        # Determine book is Kindle Unlimited or not
        kindle_or_cost = kindle_unlimited_or_not(first_page_soup)
        
        # Provide link of where to download cover page, or download it
        bookcover_url = download_book_cover(first_page_soup)
        
        return star_rating, ratings_count, reviews_count, page_count, publish_date, summary, genre_list, kindle_or_cost, bookcover_url
        
    finally:
        # Close the browser window
        driver.quit()

# Collect Rating stars and number of reviews
def collect_rating_and_reviews(soup):
    star_rating = soup.find_all('div', {'class': "RatingStatistics__rating"})
    star_rating_text = star_rating[0].get_text()
    final_star_rating_text = str(star_rating_text) + " average rating out of 5 stars"
    
    ratings_count = soup.find_all('span', {'data-testid':"ratingsCount"})
    ratings_count_text = ratings_count[0].get_text()
    
    reviews_count = soup.find_all('span', {'data-testid':"reviewsCount"})
    reviews_count_text = reviews_count[0].get_text()
    
    return(final_star_rating_text, ratings_count_text, reviews_count_text)

# Collect number of pages and date published
def collect_page_and_publish_date(soup):
    page_count = soup.find_all('p', {'data-testid': "pagesFormat"})
    page_count_text = page_count[0].get_text()
    
    publish_date = soup.find_all('p', {'data-testid':"publicationInfo"})
    publish_date_text = publish_date[0].get_text()
    
    return(page_count_text, publish_date_text)

# Collect summary
def collect_summary(soup):
    summary = soup.find_all('div', {'data-testid':"description"})
    summary_text = summary[0].get_text()
    summary_text = summary_text[:-len("Show more")]
    
    return(summary_text)

# Collect genres
def collect_genres(soup):
    genre_list = []
    genres = soup.find_all('span', {'class':"BookPageMetadataSection__genreButton"})
    
    for genre in genres:
        genre_name = genre.get_text()
        genre_list.append(genre_name)
    
    return(genre_list)

# Determine book is Kindle Unlimited or not
def kindle_unlimited_or_not(soup):
    cost = soup.find_all('button', {'class':"Button Button--buy Button--medium Button--block"})
    cost_text = cost[0].get_text()

    if 'Kindle Unlimited' in cost_text:
        display_cost_text = 'Book is on Kindle Unlimited'

        return(display_cost_text)
    else:
        cost_text = cost_text[len("Kindle"):]
        display_cost_text = 'Book is not on Kindle Unlimited. Cost is: ' + cost_text

        return(display_cost_text)

# Download book cover or provides link to download book cover
def download_book_cover(soup):
    book_cover = soup.find_all('div', {'class':"BookCover__image"})
        
    book_cover_src = book_cover[0].find('img', attrs={'role':'presentation'})
    book_cover_url = book_cover_src['src']
    
    return(book_cover_url)

    # Downloads book cover
    #response = requests.get(book_cover_url)
    #with open(search_query + '_book_cover.jpg', 'wb') as f:
        #f.write(response.content)
        
def write_output_to_file(good_reads_folder, output_file_name, *args):
    output_folder = good_reads_folder + "/" + output_file_name
    os.makedirs(output_folder, exist_ok=True)
    
    output_file_path = f"{output_folder}/{output_file_name}.txt"
    
    with open(output_file_path, 'w') as output_file:
        for arg in args:
            print(arg, file=output_file)
            
    response = requests.get(bookcover_url)
    if response.status_code == 200:
        file_path = os.path.join(output_folder, f"{text_file_name}_book_cover.jpg")
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Book cover saved to {file_path}")
    else:
        print(f"Failed to fetch book cover. Status code: {response.status_code}")
            
    print(f"Output has been written to: {output_file_path}")

if __name__ == "__main__":
    
    # Output folder
    goodreads_folder = "C:/Users/alame/Documents/python_dev/Goodreads"
        
    # Start the timer
    start_time = time.time()
    
    print("\nWelcome to Goodreads Webscraper!\n")
    author = input("Enter the authors name: \n")
    book_title = input("Enter the book you want to search: \n")
    
    search_query = book_title + " by " + author

    star_rating, ratings_count, reviews_count, page_count, publish_date, summary, genre_list, kindle_or_cost, bookcover_url = search_goodreads(search_query)
    
    text_file_name = search_query.lower()
    text_file_name = text_file_name.replace(" ", "_")
    
    # Formatting
    search_query_final = "Query: \n" + search_query + "\n\n"
    star_rating_final = "Star Rating: \n" + star_rating + "\n\n"
    ratings_count_final = "Total Ratings: \n" + ratings_count + "\n\n"
    reviews_count_final = "Total Reviews: \n" + reviews_count + "\n\n"
    page_count_final = "Page Count: \n" + page_count + "\n\n"
    publish_date_final = "Publish Date: \n" + publish_date + "\n\n"
    summary_final = "Summary: \n" + summary + "\n\n"
    genre_list_final = "Genre List: \n" + str(genre_list) + "\n\n"
    kindle_or_cost_final = "Kindle or Cost: \n" + kindle_or_cost + "\n\n"
    
    write_output_to_file(goodreads_folder, text_file_name, search_query_final, star_rating_final, 
                         ratings_count_final, reviews_count_final, page_count_final, 
                         publish_date_final, summary_final, genre_list_final, 
                         kindle_or_cost_final, bookcover_url)
    
    # Stop the timer
    end_time = time.time()
    
    # Calculated time
    print(f"Elapsed time: {end_time-start_time:.2f} seconds")
    