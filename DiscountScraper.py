import re
import time
import asyncio
import sqlite3
import pyppeteer

LOGIN_PAGE = "https://start.telebank.co.il/login/#/LOGIN_PAGE"
BASE_URL = "https://start.telebank.co.il/"
HOME_PAGE = "apollo/core/templates/RETAIL/masterPage.html#/MY_ACCOUNT_HOMEPAGE"
OSH_PAGE = "apollo/core/templates/RETAIL/masterPage.html#/OSH_LENTRIES_ALTAMIRA"
CREDIT_PAGE = "apollo/core/templates/RETAIL/masterPage.html#/CARD_DEBIT_TRANSACTION"

WAIT_INTERVAL = 0.1

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

async def get_table(page):    
    i = 0
    while True:   
        try:
            x = await page.evaluate('document.querySelectorAll("[id=rc-table-row-%d]")[1].innerText'%i, force_expr=True)
            print(x)
            i += 1
        except pyppeteer.errors.ElementHandleError:
            break;  

async def get_last_transactions():
    
    browser = await pyppeteer.connect(browserWSEndpoint  = "ws://127.0.0.1:9222/devtools/browser/879e79c8-aeea-4a79-af18-19512c88567b")
    page = (await browser.pages())[0]

    #await get_table(page)

    #await go_and_wait_url( page, f"{BASE_URL}{CREDIT_PAGE}" )

       
    await page.click('#dateFilter')
    await page.click('#appDropDown-1')
    
    

    await get_table(page)

async def main():
    await get_last_transactions()

asyncio.get_event_loop().run_until_complete(main())