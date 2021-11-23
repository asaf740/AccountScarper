import re
import time
import asyncio
import getpass
import sqlite3
import pyppeteer




#google-chrome --remote-debugging-port=9222 --user-data-dir=/home/user/chrome

LOGIN_PAGE = "login/#/LOGIN_PAGE"
BASE_URL = "https://start.telebank.co.il/"
HOME_PAGE = "apollo/core/templates/RETAIL/masterPage.html#/MY_ACCOUNT_HOMEPAGE"
OSH_PAGE = "apollo/core/templates/RETAIL/masterPage.html#/OSH_LENTRIES_ALTAMIRA"
CREDIT_PAGE = "apollo/core/templates/RETAIL/masterPage.html#/CARD_DEBIT_TRANSACTION"

WAIT_INTERVAL = 0.3

OUTPUT_DB = "account.db"

class SQLite():
    def __init__(self, file):
        self.file=file
    def __enter__(self):
        self.conn = sqlite3.connect(self.file)
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor()
    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.conn.close()

async def get_current_url(page):
    return (await page.evaluate("() => window.location.href"))

async def wait_navigation( browser, url ):
    while True:
        page = (await browser.pages())[0]
        cur_url = await get_current_url(page)
        if cur_url == url:
            return
        
        time.sleep( WAIT_INTERVAL )    

async def wait_url( page, url ):
    while True:
        cur_url = await get_current_url(page)
        if cur_url == url:
            return
        
        time.sleep( WAIT_INTERVAL )

async def go_and_wait_url( page, url ):
    await page.goto(url)
    while True:
        cur_url = await get_current_url(page)
        if cur_url == url:
            return
        time.sleep( WAIT_INTERVAL )       


async def login(page):
    await page.goto( f"{BASE_URL}{LOGIN_PAGE}" )
    
    
    id =  input("tz: ")
    password = getpass.getpass("password: ")
    idnum = input("id: ")
    await page.type('input[name=tzId]', id, delay = 20)
    await page.type('input[name=tzPassword]', password, delay = 20)
    await page.type('input[name=aidnum]', idnum, delay = 20)
    await page.click('.sendBtn')
    await page.waitForNavigation()

class TableDumper:
    def __init__(self, page, db_path):
        self.page = page
        self.db_path = db_path
        
    def create_table( self, table_name ):
        self.table_name = table_name
        with SQLite(self.db_path) as cur:
            create_command = f""" CREATE TABLE IF NOT EXISTS {self.table_name} (date text, value_date text, description text, amount real)"""
            cur.execute( create_command )

    def insert_row_to_db(self, row ):
        with SQLite(self.db_path) as cur:
            insert_command = f""" INSERT INTO {self.table_name} values (?, ?, ?, ?)"""
            cur.execute( insert_command, row.split("\n")[:4] )

    async def dump_url_to_db( self ):
        i = 0
        while True:   
            try:
                row = await self.page.evaluate('document.querySelectorAll("[id=rc-table-row-%d]")[1].innerText'%i, force_expr=True)
                self.insert_row_to_db( row )
                i += 1
            except pyppeteer.errors.ElementHandleError:
                break;  

async def get_account_transactions(page):
    
    await go_and_wait_url( page, f"{BASE_URL}{OSH_PAGE}" )
            
    td = TableDumper(page, OUTPUT_DB)
    td.create_table( "osh" )
    await td.dump_url_to_db() 
    


async def get_credit_transactions(page):
    await go_and_wait_url( page, f"{BASE_URL}{CREDIT_PAGE}" )
    await page.waitForSelector('#dateFilter', visible = True)
    await page.click('#dateFilter')
    await page.waitForSelector('#appDropDown-1', visible = True)
    await page.click('#appDropDown-1')
    time.sleep(5)
    
    td = TableDumper(page, OUTPUT_DB)
    td.create_table( "osh" )
    await td.dump_url_to_db()     

async def get_last_transactions():

    browser = await pyppeteer.launch( headless = False, ignoreHTTPSErrors = True, args = [
      "--unlimited-storage",
      "--full-memory-crash-report",
      "--disable-gpu",
      "--ignore-certificate-errors",
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--lang=en-US;q=0.9,en;q=0.8",
      "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    ])    
    page = (await browser.pages())[0]
    
    await login(page)
    
    #browser = await pyppeteer.connect(browserWSEndpoint  = "ws://127.0.0.1:9222/devtools/browser/6783c4cf-5aae-488c-abf6-15bccca86c81")
    #page = (await browser.pages())[0]

    print("getting osh data")
    await get_account_transactions(page)
    
    print("getting credit cards data")
    await get_credit_transactions(page)
    
    print("closing")
    await browser.close()
    

async def main():
    await get_last_transactions()

asyncio.get_event_loop().run_until_complete(main())