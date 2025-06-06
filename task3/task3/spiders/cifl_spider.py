'''
The next one is: https://cifl.com/annuaire.htm?lang=EN. For this one you'll have to go to the sub links to scrape the data.
Fields required: company_name , contact_name, phone, website and address

'''

from pathlib import Path
import scrapy


class CiflSpider(scrapy.Spider):
    name = 'cifl'
    start_urls = ['https://cifl.com/annuaire.htm?lang=EN']
    custom_settings = {
        'LOG_LEVEL': 'ERROR',  # Only show errors
        'LOG_ENABLED': False,
        'DOWNLOAD_DELAY': 1,  # 2 second delay between requests
        'RANDOMIZE_DOWNLOAD_DELAY': 0.2,  # 0.5 * to 1.5 * DOWNLOAD_DELAY
        'CONCURRENT_REQUESTS': 1,
    }
    count= 0
    def parse(self, response):
        # print(f"Parsing URL: {response.url}")
        table = response.css('table.table.table-striped')
        
        
        for i in table.css('tr')[2:]:
            company_name = i.css('td a::text').get()
            company_url = i.css('td')[1].css('a::text').get()
            detail_link = f"https://cifl.com/{i.css('td')[0].css('a::attr(href)').get()}"
            
            yield response.follow(detail_link, callback=self.parse_detail,
                                  meta={'company_name': company_name, 'company_url': company_url})
            
    def parse_detail(self, response):
        # print(f"Parsing detail URL: {response.url}")
        company_name = response.meta['company_name']
        company_url = response.meta['company_url']
        info = response.css('div.col-sm-9.col-md-9.main').css('p')[0].css('::text').getall()
        
        contact_name = info[1]
        phone = info[4]
        address = info[10] if len(info) > 10 and info[10].strip() else (info[9] if len(info) > 9 and info[9].strip() else None)
        
        # print(f"Contact Name: {contact_name}, Phone: {phone}, Address: {address}")

        yield {
            'count': self.count,
            'company_name': company_name,
            'contact_name': contact_name,
            'phone': phone,
            'website': company_url,
            'address': address
        }
        self.count += 1