# -*- coding: utf-8 -*-
# general purpose template
# + variation of 'mcpremium'
# + output format changed according to 'ali_premium.h_off_companies'
# + focus is set to all members instead of only premium members

from madeinchina.common import *

BaseURL     = "https://www.made-in-china.com"
TargetURL   = BaseURL + "/quick-manufacturers/index/0-A.html"
CompanyArr   = []

class McpremiumSpider(Spider):
    name = 'mcallmembers'
    start_urls = [ TargetURL ]
    custom_settings = {
        'ITEM_PIPELINES' : {
            'madeinchina.pipelines.MadeinchinaAllMembersAPIlPipeline': 300
            # 'madeinchina.pipelines.MadeinchinaPremiumExcelPipeline': 300
        },
        'DOWNLOADER_MIDDLEWARES' : {
            # 'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            # 'madeinchina.middlewares.RandomUserAgentMiddleware': 400,
            'madeinchina.middlewares.RandomProxyForBlockedUrls': 650,
            'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
            'rotating_proxies.middlewares.BanDetectionMiddleware': 620
        },
        'FEED_EXPORT_ENCODING'              :   'utf-8',
        'LOG_ENABLED'                       :   True,
        'ROBOTSTXT_OBEY'                    :   False,
        'COOKIES_ENABLED'                   :   False,
        'TELNETCONSOLE_ENABLED'             :   False,
        'HTTPCACHE_ENABLED'                 :   False,
        'COMPRESSION_ENABLED'               :   True,
        'HTTPCACHE_GZIP'                    :   False,
        'DOWNLOAD_TIMEOUT'                  :   30,
        'RETRY_TIMES'                       :   30,
        'DOWNLOAD_DELAY'                    :   0,
        'CONCURRENT_REQUESTS'               :   16,
        'CONCURRENT_REQUESTS_PER_DOMAIN'    :   8,
        'CONCURRENT_REQUESTS_PER_IP'        :   8,
        'ROTATING_PROXY_PAGE_RETRY_TIMES'   :   120,
        'ROTATING_PROXY_LIST_PATH'          :   'proxylist.txt',
        'DOWNLOAD_HANDLERS'                 :   {'s3': None}
    }

    def start_requests(self):
        mymeta = { 'proxy': 'http://103.196.233.199:8080' }
        yield Request(TargetURL, callback=self.parse, meta=mymeta, priority=10)
    
    def parse(self, response):
        for alphabets in response.xpath("//div[@id='alp']//a"):
            alpha_url = response.urljoin(alphabets.xpath("./@href")[0].extract())
            yield Request(alpha_url, callback=self.alphapg, meta=response.meta, priority=20)
    
    def alphapg(self, response):
        for companies in response.xpath("//div[@class='qpList']//a"):
            keyword_url = response.urljoin( companies.xpath("./@href")[0].extract() )
            yield Request(keyword_url, callback=self.listingpg, meta=response.meta, priority=30)
        try:
            next_page = response.urljoin( response.xpath("//div[@id='pager']//a[text()='Next']/@href")[0].extract() )
            yield Request(next_page, callback=self.alphapg, meta=response.meta, priority=20)
        except:
            pass
    
    def listingpg(self, response):
        global CompanyArr
        for records in response.xpath("//div[@class='search-list']/div[contains(@class,'list-node')]"):
            company_url = response.urljoin(records.xpath("./h2/a/@href")[0].extract())
            try:
                business_type = bs(records.xpath("//td[@class='subject' and contains(text(),'Business Type')]/following-sibling::td[1]")[0].extract(), "html.parser").get_text(strip=True)
                business_type = sub(r"\s{2,}", "\s", business_type).strip()
            except:
                business_type = "-"
            try:
                main_products = bs(records.xpath("//td[@class='subject' and contains(text(),'Main Products')]/following-sibling::td[1]")[0].extract(), "html.parser").getText(strip=True)
                main_products = sub(r"\s{2,}", " ", main_products).strip()
                main_products = main_products.replace(" ,", ",")
                main_products = main_products.encode("unicode-escape").decode()
            except:
                main_products = "-"
            try:
                mgmt_certification = bs(records.xpath("//td[@class='subject' and contains(text(),'Mgmt. Certification')]/following-sibling::td[1]")[0].extract(), "html.parser").get_text(strip=True)
                mgmt_certification = mgmt_certification.encode("unicode-escape").decode()
            except:
                mgmt_certification = "-"
            try:
                province = bs(records.xpath("//td[@class='subject' and contains(text(),'Province')]/following-sibling::td[1]")[0].extract(), "html.parser").get_text(strip=True)
                province = province.encode("unicode-escape").decode()
            except:
                province = "-"
            memberships = []
            for membershipz in response.xpath(".//div[@class='compnay-auth']//span"):
                memship = bs( membershipz.extract(), "html.parser" ).get_text(strip=True)
                if not memship in memberships:
                    memberships.append(memship)
            response.meta['company_url'] = company_url
            response.meta['business_type'] = business_type
            response.meta['main_products'] = main_products
            response.meta['mgmt_certification'] = mgmt_certification
            response.meta['province'] = province
            response.meta['memberships'] = ",".join(memberships)
            contact_page = company_url + "/contact-info.html"
            print ("company_url = %s" % company_url)
            # validate if profile is already posted
            if company_url != "-":
                if not company_url in CompanyArr:
                    CompanyArr.append( company_url )
                    print ("Adding company: %s" % company_url)
                    post_status = validate_profile( company_url )
                    if (post_status == False):
                        print ("Validated comapny: %s" % company_url )
                        yield Request( contact_page, callback=self.contactpg, meta=response.meta, priority=40 )
        try:
            next_page = response.urljoin( response.xpath("//div[@class='pager']//a[@class='next']/@href")[0].extract() )
            yield Request(next_page, callback=self.listingpg, meta=response.meta, priority=30)
        except:
            pass
    
    def contactpg(self, response):
        try:
            address = bs(response.xpath("//span[@class='contact-address']")[0].extract(), "html.parser").get_text(strip=True)
            address = sub(r"\s{2,}", "\s", address).strip()
            address = address.encode("unicode-escape").decode()
        except:
            address = "-"
        try:
            telephone = bs(response.xpath("//div[@class='info-label' and contains(text(),'Telephone')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            telephone = "-"
        try:
            mobile_phone = bs(response.xpath("//div[@class='info-label' and contains(text(),'Mobile Phone')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            mobile_phone = "-"
        try:
            fax = bs(response.xpath("//div[@class='info-label' and contains(text(),'Fax')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            fax = "-"
        website = "-"
        try:
            website_raw = response.urljoin( response.xpath("//div[@class='info-label' and contains(text(),'Website')]/following-sibling::div[contains(@class,'field')]/a/@href")[0].extract() )
            if len(website_raw) > 2:
                try:
                    website = requests.get(website_raw,timeout=10,allow_redirects=True, proxies={ 'https': '%s' % response.meta['proxy'] }).url
                except:
                    pass
        except:
            pass
        try:
            contact_person = bs(response.xpath("//span[@class='sr-sendMsg-name']")[0].extract(), "html.parser").get_text(strip=True)
            contact_person = contact_person.encode("unicode-escape").decode()
        except:
            contact_person = "-"
        try:
            department = response.xpath("//div[contains(@class,'-customer-info')]/div[@class='info-detail']/div[@class='info-item'][1]/text()")[0].extract()
            department = department.encode("unicode-escape").decode()
        except:
            department = "-"
        try:
            job_title = response.xpath("//div[contains(@class,'-customer-info')]/div[@class='info-detail']/div[@class='info-item'][2]/text()")[0].extract()
            job_title = job_title.encode("unicode-escape").decode()
        except:
            job_title = "-"
        try:
            membership_year = response.xpath("//span[@class='txt-year']/text()")[0].extract()
        except:
            membership_year = "-"
        response.meta['address'] = address
        response.meta['telephone'] = telephone
        response.meta['mobile_phone'] = mobile_phone
        response.meta['fax'] = fax
        response.meta['website'] = website
        response.meta['contact_person'] = contact_person
        response.meta['department'] = department
        response.meta['job_title'] = job_title
        response.meta['membership_year'] = membership_year
        try:
            aboutus_page = response.urljoin(response.xpath("//ul[contains(@class,'-nav-main')]//a[contains(text(),'About Us') and contains(@class,'title')]/@href")[0].extract())
            yield Request( aboutus_page, callback=self.aboutuspg, meta=response.meta, priority=50 )
        except:
            pass
    
    def aboutuspg(self, response):
        try:
            company_title = bs(response.xpath("//div[contains(@class,'-title-comName')]//h1")[0].extract(), "html.parser").get_text(strip=True)
        except:
            company_title = "-"
        try:
            registered_capital = response.xpath("//td/span[contains(@class,'info-label') and contains(.,'Registered Capital')]/ancestor::td[1]/following-sibling::td[1]/@title")[0].extract()
        except:
            registered_capital = "-"
        try:
            sgs_serial = bs(response.xpath("//span[contains(@class,'num-item') and contains(text(),'SGS Serial')]/span")[0].extract(), "html.parser").get_text(strip=True)
        except:
            sgs_serial = "-"
        images = []
        for imagez in response.xpath("//div[@class='swiper-wrapper']//img[not(@origsrc='')]"):
            try:
                img = response.urljoin( imagez.xpath("./@origsrc")[0].extract() )
                if not img in images:
                    images.append(img)
            except:
                pass
        try:
            description = response.xpath("//div[contains(@class,'comProfile')]/p[contains(@class,'intro-cnt')]")[0].extract()
            description = escape( description )
        except:
            description = "-"
        try:
            commercial_terms = bs(response.xpath("//div[contains(@class,'label') and contains(.,'International Commercial Terms')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            commercial_terms = "-"
        try:
            payment_terms = bs(response.xpath("//div[contains(@class,'label') and contains(.,'Terms of Payment')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            payment_terms = "-"
        average_lead_time = "-"
        try:
            average_lead_time = bs(response.xpath("//div[contains(@class,'label') and contains(.,'Average Lead Time')]/following-sibling::div[1]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            pass
        trade_employees = "-"
        try:
            trade_employees = bs(response.xpath("//div[contains(@class,'label') and contains(.,'Number of Foreign Trading')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            pass
        try:
            export_percentage = bs(response.xpath("//div[contains(@class,'label') and contains(.,'Export Percentage')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            export_percentage = "-"
        main_markets = "-"
        try:
            main_markets = bs(response.xpath("//div[contains(@class,'label') and contains(.,'Main Market')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            pass
        nearest_port = "-"
        try:
            nearest_port = bs(response.xpath("normalize-space(//div[contains(@class,'label') and contains(.,'Nearest Port')]/following-sibling::div[contains(@class,'field')])")[0].extract(), "html.parser").get_text()
        except:
            pass
        try:
            import_export_mode = response.xpath("//div[contains(@class,'label') and contains(.,'Import & Export Mode')]/following-sibling::div[contains(@class,'field')]")[0].extract()
            import_export_mode = escape( import_export_mode )
        except:
            import_export_mode = "-"
        try:
            factory_address = bs(response.xpath("//div[contains(@class,'label') and contains(.,'Factory Address')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
            factory_address = factory_address.encode("unicode-escape").decode()
        except:
            factory_address = "-"
        try:
            research_capacity = bs(response.xpath("//div[contains(@class,'label') and contains(.,'R&D Capacity')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            research_capacity = "-"
        try:
            research_staff = bs(response.xpath("//div[contains(@class,'label') and contains(.,'R&D Staff')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            research_staff = "-"
        try:
            production_lines = bs(response.xpath("//div[contains(@class,'label') and contains(.,'Production Lines')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            production_lines = "-"
        try:
            annual_output_value = bs(response.xpath("//div[contains(@class,'label') and contains(.,'Annual Output Value')]/following-sibling::div[contains(@class,'field')]")[0].extract(), "html.parser").get_text(strip=True)
        except:
            annual_output_value = "-"
        response.meta['company_title'] = company_title
        response.meta['registered_capital'] = registered_capital
        response.meta['sgs_serial'] = sgs_serial
        response.meta['images'] = ",".join(images)
        response.meta['description'] = description
        response.meta['commercial_terms'] = commercial_terms
        response.meta['payment_terms'] = payment_terms
        response.meta['average_lead_time'] = average_lead_time
        response.meta['trade_employees'] = trade_employees
        response.meta['export_percentage'] = export_percentage
        response.meta['main_markets'] = main_markets
        response.meta['nearest_port'] = nearest_port
        response.meta['import_export_mode'] = import_export_mode
        response.meta['factory_address'] = factory_address
        response.meta['research_capacity'] = research_capacity
        response.meta['research_staff'] = research_staff
        response.meta['production_lines'] = production_lines
        response.meta['annual_output_value'] = annual_output_value
        yield response.meta
