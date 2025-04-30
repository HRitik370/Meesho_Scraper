# Meesho Scraper API

A FastAPI-based web scraper for Meesho products with delivery date checking.

## Features

- Search products on Meesho
- Check delivery dates for products
- Login support for authenticated scraping
- CSV export of scraped data
- Persistent storage using SQLite

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the API: `python app.py`
4. Access the API documentation: http://localhost:8000/docs

## API Endpoints

- `/setup-login/`: Setup Chrome profile with manual login
- `/search/`: Search for products and check delivery dates
- `/download-csv/`: Download scraped data as CSV