import re
import time
import asyncio
import sqlite3
import pyppeteer


#google-chrome --remote-debugging-port=9222 --user-data-dir=/home/user/chrome

LOGIN_PAGE = "https://start.telebank.co.il/login/#/LOGIN_PAGE"
BASE_URL = "https://start.telebank.co.il/"
HOME_PAGE = "apollo/core/templates/RETAIL/masterPage.html#/MY_ACCOUNT_HOMEPAGE"
OSH_PAGE = "apollo/core/templates/RETAIL/masterPage.html#/OSH_LENTRIES_ALTAMIRA"
CREDIT_PAGE = "apollo/core/templates/RETAIL/masterPage.html#/CARD_DEBIT_TRANSACTION"

WAIT_INTERVAL = 0.1

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


async def login():
    browser = await pyppeteer.launch( headless = False )    
    page = await browser.newPage()
    await page.goto( LOGIN_PAGE )
    await page.type('input[name=tzId]', '123456780', delay = 20)
    await page.type('input[name=tzPassword]', '123456789', delay = 20)
    await page.type('input[name=aidnum]', '123456789', delay = 20)
    await page.click('.sendBtn')
    time.sleep(3)

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

    async def dump_url_to_db( self, url ):
        #await go_and_wait_url(url)
        i = 0
        while True:   
            try:
                row = await self.page.evaluate('document.querySelectorAll("[id=rc-table-row-%d]")[1].innerText'%i, force_expr=True)
                self.insert_row_to_db( row )
                i += 1
            except pyppeteer.errors.ElementHandleError:
                break;  


async def get_table(page):
    # with SQLite(DB_FILE) as cur:
    
    #     create_day_time_table(cur)
        
    #     assert( len(data) %DAY_TIME_RECORD_WIDTH == 0)
    
    #     for i in range(DAY_TIME_RECORD_WIDTH, len(data), DAY_TIME_RECORD_WIDTH):
    #         insert_cmd = build_insert_cmd( year, month, data[i:i+DAY_TIME_RECORD_WIDTH])
    #         cur.execute( insert_cmd )

    i = 0
    while True:   
        try:
            x = await page.evaluate('document.querySelectorAll("[id=rc-table-row-%d]")[1].innerText'%i, force_expr=True)
            print(x)
            i += 1
        except pyppeteer.errors.ElementHandleError:
            print("exception %d"%i)
            break;  

async def get_last_transactions():
    
    browser = await pyppeteer.connect(browserWSEndpoint  = "ws://127.0.0.1:9222/devtools/browser/72298655-0e00-46c8-986c-c7bbf20e981f")
    page = (await browser.pages())[0]

    #await get_table(page)

    td = TableDumper(page, OUTPUT_DB)
    td.create_table( "osh" )
    await td.dump_url_to_db( f"{BASE_URL}{OSH_PAGE}" )

    #await go_and_wait_url( page, f"{BASE_URL}{CREDIT_PAGE}" )

       
    #await page.click('#dateFilter')
    #await page.click('#appDropDown-1')
    #await get_table(page)

async def main():
    await get_last_transactions()

asyncio.get_event_loop().run_until_complete(main())