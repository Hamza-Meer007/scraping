import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


'''
Cert ID, legal business name, DBA Name, Address, email, number of employees, office phone

https://caleprocure.ca.gov/pages/PublicSearch/supplier-search.aspx

'''
count = 0
with open('data.jsonl', 'w') as f:
    with sync_playwright() as p:
        # Launch browser (Chromium, Firefox, or WebKit)
        browser = p.chromium.launch(headless=True)  # Set headless=False to see the browser
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.set_default_timeout(90000)  # Set a timeout for page operations
        # Navigate to the URL
        page.goto('https://caleprocure.ca.gov/pages/PublicSearch/supplier-search.aspx')
        
        # Get the full page content after JS execution
        content = page.content()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        # form = soup.find_all('form')[0]
        
        # main_div  = form.find_all('div')[1].find_all('div')[1]
        
        # form_div = main_div.find_all('div')[0].find_all('div')[1]
        
        
        page.click("input[id='ZZ_PUBSRCH1_WRK_BUTTON'], button[data-if-label='SearchButton']")
        print("Clicked the search button")

        page.wait_for_load_state('networkidle')
        data = page.content()
        soup2 = BeautifulSoup(data, 'html.parser')
        form = soup2.find_all('form')[0]
        main_div = form.find_all('div')[1].find_all('div')[1].find('div',{'id':"ZZ_PUBSRCH_VW$scrolli$0"})
        
        lists = main_div.find_all('div')[1].find('ul',class_='list-group')

        links = lists.find_all('a')
        for i in links[1:]:
            link_id = i.get('id')
            print(f"Processing link with ID: {link_id}")

            locator = page.locator(f"a[id='{link_id}']")
            try:
                locator.wait_for(state="visible", timeout=10000)
                with page.expect_navigation(wait_until="networkidle"):
                    locator.click()
            except Exception as e:
                print(f"Failed to click link with ID {link_id}: {e}")
                continue

            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(5000)
            
            if "Certification Profile" in page.title():
                print("Successfully loaded certification profile page")
            else:
                print(f"Current page title: {page.title()}")
            # Get the response page content
            detail_content = page.content()
            detail_soup = BeautifulSoup(detail_content, 'html.parser')
    
            
            
            
            main = detail_soup.find_all('form')[0].find('div',class_='form-horizontal').find_all('div')[1].find_all('div')[1].find_all('div')[0]
            
            all_spans= main.find_all('span')
            cert_id = all_spans[1].text.strip()
            legal_business_name = all_spans[2].text.strip()
            dba_name1 = all_spans[3].text.strip()
            address = all_spans[8].text.strip().replace('\n', ' ')
        
            phone = all_spans[5].text.strip()
            employee_num = all_spans[9].text.strip()
            email = main.find('a').text.strip()
            
            data = {
                'count':count,
                "cert_id": cert_id,
                "legal_business_name": legal_business_name,
                "dba_name": dba_name1,
                "address": address,
                "email": email,
                "number_of_employees": employee_num,
                "office_phone": phone
            }
            
            f.write(json.dumps(data) + '\n')
            count += 1


        # Go back to the search results page
            try:
                page.go_back(wait_until='networkidle')
                page.wait_for_timeout(3000)  # wait for content to load
            except Exception as e:
                print(f"Failed to navigate back: {e}")
                break
                # or continue depending on your preference

            # Re-fetch the updated page content and BeautifulSoup
            data = page.content()
            soup2 = BeautifulSoup(data, 'html.parser')
            form = soup2.find_all('form')[0]
            main_div = form.find_all('div')[1].find_all('div')[1].find('div', {'id': "ZZ_PUBSRCH_VW$scrolli$0"})
            lists = main_div.find_all('div')[1].find('ul', class_='list-group')
            links = lists.find_all('a')

            
        
        
        
        browser.close()