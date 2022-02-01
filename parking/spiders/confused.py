from scrapy.crawler import CrawlerProcess
import scrapy
from scrapy.utils.project import get_project_settings
from scrapy_splash import SplashRequest
from scrapy.loader import ItemLoader


script = """
function main(splash)
  local url = splash.args.url
  local content = splash.args.content
  assert(splash:set_content(content, "text/html; charset=utf-8", url))
  -- assert(splash:runjs('document.getElementsByClassName("btn-next")[0].children[0].click()'))
  assert(splash:runjs('ctrl.set_pageReload(ctrl.context.cur_page + 1)'))
  assert(splash:runjs('window.notReloaded = 1'))
  -- assert(splash:wait(2)) -- Optional initial wait time
  local exit = false
  while (exit == false)
  do
    result, error = splash:wait_for_resume([[
      function main(splash) {
        window.notReloaded ? splash.error() : splash.resume();
      }
    ]])
    if result then
      exit = true
    else
      splash:wait(0.2) -- Adjust resolution as desired
    end
  end
  assert(splash:wait_for_resume([[
    function main(splash) {
      $(() => splash.resume());
    }
  ]]))
  return {html = splash:html()}
end"""

class parkingSpider(scrapy.Spider):
    name = 'parking'
    start_urls= ['https://www.theparking.eu/used-cars/.html']

    def parse(self, response, **kwargs):
        section = response.css('li.li-result')
        #for item in section:
        #    yield {
        #        'manufacturer': item.css('span.brand::text').extract_first(),
        #        'model': item.css('span.sub-title::text').extract_first(),
        #        'engine_size': item.css('span.nowrap::text').extract_first(),
        #        'model_type': item.css('span span.nowrap::text').extract_first(),
        #        'old_price': item.css('li.li-result p.old-prix span::text').extract_first(),
        #        'price': item.css('li.li-result p.prix::text').extract_first(),
        #        'consumption': item.css('li.li-result div.desc::text').extract_first(),
        #        'date': item.css('p.btn-publication::text').extract_first(),
        #        'fuel_type': item.css('div.bc-info div.upper::text').extract_first(),
        #        'mileage': item.css('li.li-result div.bc-info ul div::text')[1].extract(),
        #        'year': item.css('li.li-result div.bc-info ul div::text')[2].extract(),
        #        'transmission_type': item.css('li.li-result div.bc-info ul div::text')[3].extract(),
        #        'add_number': item.css('li.li-result div.bc-info ul div::text')[4].extract(),
        #        'href':response.xpath('(//li[@class="btn-next"]//@href)[1]').get()
        #    }

        next_page = response.css('li.btn-next').extract_first()
        print(next_page)
        if next_page is not None:
            yield SplashRequest(
                response.url,
                self.parse,
                endpoint='execute',
                args={
                    'lua_source': script,
                    'content': response.text,
                    'wait':5,
                },
                cache_args=['lua_source'],
                dont_filter = True,)


settings = get_project_settings()
settings.update({
    'FEED_URI': 'parking.jl',
    'FEED_FORMAT': 'jsonlines'
})
process = CrawlerProcess(settings)
process.crawl(parkingSpider)
process.start()
