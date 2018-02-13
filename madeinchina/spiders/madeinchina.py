# @author:  Janib Soomro
# @e-mail:  soomrojb@gmail.com
# @skype:   soomrojb
# @dated:   13th Feb. 2018

import scrapy
from scrapy.utils.response import open_in_browser

BaseURL = "http://sourcing.made-in-china.com"
TargetURL = BaseURL + "/sourcingrequest?keyword=&excat=&region=&pdate=&sort=&page=1&way=inner&type=lastest"

class MicSpider(scrapy.Spider):
    name = 'madeinchina'
    allowed_domains = [BaseURL]
    start_urls = [TargetURL]

    def parse(self, response):
        for Category in response.xpath("//div[@class='cat-list']/ul/li"):
            RawCat = Category.xpath("./a/@href")[0].extract()
            Title = (RawCat.split(",")[-2]).split("'")[-2]
            Code = (RawCat.split(",")[-1]).split("'")[-2]
            NewURL = TargetURL + "&cat=" + Code
            MetaData = {
                "Catg_Title"    :   Title,
                "Catg_Code"     :   Code
            }
            yield scrapy.Request(NewURL, callback=self.catparse, dont_filter=True, meta=MetaData)
            #break
    
    def catparse(self, response):
        for Posts in response.xpath("//div[contains(@class,'sc-list-buyer')]/ul[@class='sc-list-bd']/li"):
            PostTitle = Posts.xpath("normalize-space(.//h6[@class='title'])")[0].extract().strip()
            PostHref = BaseURL + Posts.xpath("normalize-space(.//h6[@class='title']/a/@href)")[0].extract()
            MetaData = {
                "Catg_Title"    :   response.meta['Catg_Title'],
                "Catg_Code"     :   response.meta['Catg_Code'],
                "Post_Title"    :   PostTitle,
                "Post_Href"     :   PostHref
            }
            yield scrapy.Request(PostHref, callback=self.postparse, dont_filter=True, meta=MetaData)

    def postparse(self, response):
        BreadCrumn = response.xpath("normalize-space(//div[@class='ellipsis-rfq-div'])")[0].extract()
        try:
            Quantity = response.xpath("normalize-space(//li/span[(@class='gray info-title') and (text()='Purchase Quantity:')]/../span[2]/text())")[0].extract()
        except:
            Quantity = "-"
        try:
            PostDate = response.xpath("normalize-space(//li/span[(@class='gray info-title') and (text()='Date Posted:')]/../span[2]/text())")[0].extract()
        except:
            PostDate = "-"
        try:
            ExpireDate = response.xpath("normalize-space(//li/span[(@class='gray info-title') and (text()='Valid to:')]/../span[2]/text())")[0].extract()
        except:
            ExpireDate = "-"
        try:
            Country = response.xpath("normalize-space(//span[(@class='long-name') and contains(text(),'Request From:')]/../../span[2]/text())")[0].extract()
        except:
            Country = "-"
        try:
            LeftQuote = response.xpath("normalize-space(//span[(contains(@class,'gray')) and (text()='Quote Left:')]/../span[2]/text())")[0].extract()
        except:
            LeftQuote = "-"
        try:
            Description = response.xpath("//div[contains(@class,'prod-info')]/div[@class='description-info']")[0].extract()
        except:
            Description = "-"
        yield {
                "Category Title"    :   response.meta['Catg_Title'],
                "Catgegory Code"    :   response.meta['Catg_Code'],
                "Post Title"        :   response.meta['Post_Title'],
                "Post Href"         :   response.meta['Post_Href'],
                "BreadCrumb"        :   BreadCrumn,
                "Purchase Quantity" :   Quantity,
                "Posting Date"      :   PostDate,
                "Valid Till"        :   ExpireDate,
                "Source Country"    :   Country,
                "Quotes Left"       :   LeftQuote,
                "Description HTML"  :   Description
        }
