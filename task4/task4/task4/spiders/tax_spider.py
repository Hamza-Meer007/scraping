'''
https://www.tsbpa.texas.gov/php/fpl/indlookup.php





5:51
Scrape only for Anderson county.
5:53
This is supposed to be tricky. My suggestion is to use requests and beautifulsoup for debugging. Then make a scrapy spider of it.
5:56
- Certificate Last Name
- City
- State
- Date Certified
- Date License Expiration
- Status
- Firms in which the individual is a partner, shareholder, owner, officer, director, or resident manager (This is just one string, no need to extract further details from it)

'''


from pathlib import Path
import scrapy


class TaxSpider(scrapy.Spider):
    name='tax'
    start_urls = [
        'https://www.tsbpa.texas.gov/php/fpl/indlookup.php'
    ]
    count = 0
   
        
    

    def parse(self, response):
        
       
        form_data ={}
        for i in response.css('form').css('input'):
            name  = i.css('::attr(name)').get()
            value = i.css('::attr(value)').get() or ''
            if name :
                form_data[name]= value
        
        form_data.update({
            'CNTY': 'ANDERSON',
            'list': 'fromsel',
            'submit': 'Submit Search',
            'LICID': '',
            'LNAME': '',
            'FNAME': '',
            'CLNAME': '',
            'CITY': '',
            'STATE': '',
            'ZIP': ''
        })
        # Submit the form
        return scrapy.FormRequest.from_response(
            response,
            formdata=form_data,
            callback=self.parse_results
        )
    def parse_results(self, response):
        rows = response.css('table#results').css('tr')
        for row in rows:
            link = row.css('a::attr(href)').get()
            if link:
                full_link = response.urljoin(link)
                
                yield scrapy.Request(url= full_link,callback=self.parse_detail)
                
    def parse_detail(self, response):
        # Extract the required fields from the detail page 
        certificate_last_name = response.css('table tr td::text').getall()[16]
        city = response.css('table tr td::text').getall()[18].split(',')[0].strip()
        state = response.css('table tr td::text').getall()[18].split(',')[1].strip()
        date_certified = response.css('table tr td::text').getall()[22]
        expiration_date = response.css('table tr td::text').getall()[25]
        status = response.css('table tr td::text').getall()[28]
        firms = response.css('table tr td::text').getall()[39]
            

        yield {
            'count': self.count,
            'certificate_last_name': certificate_last_name,
            'city': city,
            'state': state,
            'date_certified': date_certified,
            'date_license_expiration': expiration_date,
            'status': status,
            'firms': firms
        }
        self.count += 1