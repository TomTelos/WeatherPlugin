from . import _
from xml.etree.cElementTree import fromstring as cet_fromstring
from twisted.internet import defer
from twisted.web.client import getPage, downloadPage
from enigma import eEnv
from os import path as os_path, mkdir as os_mkdir, remove as os_remove, listdir as os_listdir
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_SKIN
from urllib import quote as urllib_quote

class WeatherIconItem:

    def __init__(self, url = '', filename = '', index = -1, error = False):
        self.url = url
        self.filename = filename
        self.index = index
        self.error = error


class MSNWeatherItem:

    def __init__(self):
        self.temperature = ''
        self.skytext = ''
        self.humidity = ''
        self.winddisplay = ''
        self.observationtime = ''
        self.observationpoint = ''
        self.feelslike = ''
        self.skycode = ''
        self.date = ''
        self.day = ''
        self.low = ''
        self.high = ''
        self.skytextday = ''
        self.skycodeday = ''
        self.shortday = ''
        self.iconFilename = ''
        self.code = ''


class MSNWeather:
    ERROR = 0
    OK = 1

    def __init__(self):
        path = '/etc/enigma2/weather_icons/'
        extension = self.checkIconExtension(path)
        if extension is None:
			path = '/usr/local/share/enigma2/weather_icons/'
			extension = self.checkIconExtension(path)
        if extension is None:
            path = os_path.dirname(resolveFilename(SCOPE_SKIN, config.skin.primary_skin.value)) + '/weather_icons/'
            extension = self.checkIconExtension(path)
        if extension is None:
            path = eEnv.resolve('${libdir}/enigma2/python/Plugins/Extensions/WeatherPlugin/icons/')
            extension = '.gif'
        self.setIconPath(path)
        self.setIconExtension(extension)
        self.initialize()
        return

    def checkIconExtension(self, path):
        filename = None
        extension = None
        if os_path.exists(path):
            try:
                filename = os_listdir(path)[0]
            except:
                filename = None

        if filename is not None:
            try:
                extension = os_path.splitext(filename)[1].lower()
            except:
                pass

        return extension

    def initialize(self):
        self.city = ''
        self.degreetype = ''
        self.imagerelativeurl = ''
        self.url = ''
        self.weatherItems = {}
        self.callback = None
        self.callbackShowIcon = None
        self.callbackAllIconsDownloaded = None
        return

    def cancel(self):
        self.callback = None
        self.callbackShowIcon = None
        return

    def setIconPath(self, iconpath):
        if not os_path.exists(iconpath):
            os_mkdir(iconpath)
        self.iconpath = iconpath

    def setIconExtension(self, iconextension):
        self.iconextension = iconextension

    def getWeatherData(self, degreetype, locationcode, city, callback, callbackShowIcon, callbackAllIconsDownloaded = None):
        self.initialize()
        language = config.osd.language.value.replace('_', '-')
        if language == 'en-EN':
            language = 'en-US'
        elif language == 'no-NO':
            language = 'nn-NO'
        self.city = city
        self.callback = callback
        self.callbackShowIcon = callbackShowIcon
        self.callbackAllIconsDownloaded = callbackAllIconsDownloaded
        url = 'http://weather.service.msn.com/data.aspx?src=vista&weadegreetype=%s&culture=%s&wealocations=%s' % (degreetype, language, urllib_quote(locationcode))
        getPage(url).addCallback(self.xmlCallback).addErrback(self.error)

    def getDefaultWeatherData(self, callback = None, callbackAllIconsDownloaded = None):
        self.initialize()
        weatherPluginEntryCount = config.plugins.WeatherPlugin.entrycount.value
        if weatherPluginEntryCount >= 1:
            weatherPluginEntry = config.plugins.WeatherPlugin.Entry[0]
            self.getWeatherData(weatherPluginEntry.degreetype.value, weatherPluginEntry.weatherlocationcode.value, weatherPluginEntry.city.value, callback, None, callbackAllIconsDownloaded)
            return 1
        else:
            return 0
            return

    def error(self, error = None):
        errormessage = ''
        if error is not None:
            errormessage = str(error.getErrorMessage())
        if self.callback is not None:
            self.callback(self.ERROR, errormessage)
        return

    def errorIconDownload(self, error = None, item = None):
        item.error = True
        if os_path.exists(item.filename):
            os_remove(item.filename)

    def finishedIconDownload(self, result, item):
        if not item.error:
            self.showIcon(item.index, item.filename)

    def showIcon(self, index, filename):
        if self.callbackShowIcon is not None:
            self.callbackShowIcon(index, filename)
        return

    def finishedAllDownloadFiles(self, result):
        if self.callbackAllIconsDownloaded is not None:
            self.callbackAllIconsDownloaded()
        return

    def xmlCallback(self, xmlstring):
        IconDownloadList = []
        root = cet_fromstring(xmlstring)
        index = 0
        self.degreetype = 'C'
        errormessage = ''
        for childs in root:
            if childs.tag == 'weather':
                errormessage = childs.attrib.get('errormessage')
                if errormessage:
                    if self.callback is not None:
                        self.callback(self.ERROR, errormessage.encode('utf-8', 'ignore'))
                    break
                self.degreetype = childs.attrib.get('degreetype').encode('utf-8', 'ignore')
                self.imagerelativeurl = '%slaw/' % childs.attrib.get('imagerelativeurl').encode('utf-8', 'ignore')
                self.url = childs.attrib.get('url').encode('utf-8', 'ignore')
            for items in childs:
                if items.tag == 'current':
                    currentWeather = MSNWeatherItem()
                    currentWeather.temperature = items.attrib.get('temperature').encode('utf-8', 'ignore')
                    currentWeather.skytext = items.attrib.get('skytext').encode('utf-8', 'ignore')
                    currentWeather.humidity = items.attrib.get('humidity').encode('utf-8', 'ignore')
                    currentWeather.winddisplay = items.attrib.get('winddisplay').encode('utf-8', 'ignore')
                    currentWeather.observationtime = items.attrib.get('observationtime').encode('utf-8', 'ignore')
                    currentWeather.observationpoint = items.attrib.get('observationpoint').encode('utf-8', 'ignore')
                    currentWeather.feelslike = items.attrib.get('feelslike').encode('utf-8', 'ignore')
                    currentWeather.skycode = '%s%s' % (items.attrib.get('skycode').encode('utf-8', 'ignore'), self.iconextension)
                    currentWeather.code = items.attrib.get('skycode').encode('utf-8', 'ignore')
                    filename = '%s%s' % (self.iconpath, currentWeather.skycode)
                    currentWeather.iconFilename = filename
                    if not os_path.exists(filename):
                        url = '%s%s' % (self.imagerelativeurl, currentWeather.skycode)
                        IconDownloadList.append(WeatherIconItem(url=url, filename=filename, index=-1))
                    else:
                        self.showIcon(-1, filename)
                    self.weatherItems[str(-1)] = currentWeather
                elif items.tag == 'forecast' and index <= 4:
                    index += 1
                    weather = MSNWeatherItem()
                    weather.date = items.attrib.get('date').encode('utf-8', 'ignore')
                    weather.day = items.attrib.get('day').encode('utf-8', 'ignore')
                    weather.shortday = items.attrib.get('shortday').encode('utf-8', 'ignore')
                    weather.low = items.attrib.get('low').encode('utf-8', 'ignore')
                    weather.high = items.attrib.get('high').encode('utf-8', 'ignore')
                    weather.skytextday = items.attrib.get('skytextday').encode('utf-8', 'ignore')
                    weather.skycodeday = '%s%s' % (items.attrib.get('skycodeday').encode('utf-8', 'ignore'), self.iconextension)
                    weather.code = items.attrib.get('skycodeday').encode('utf-8', 'ignore')
                    filename = '%s%s' % (self.iconpath, weather.skycodeday)
                    weather.iconFilename = filename
                    weather.iconFilename = filename
                    self.weatherItems[str(index)] = weather
                    if items.attrib.get('precip').encode('utf-8', 'ignore') == '':
                        index -= 1	
                    else:
                        self.showIcon(index, filename)

        if len(IconDownloadList) != 0:
            ds = defer.DeferredSemaphore(tokens=len(IconDownloadList))
            downloads = [ ds.run(download, item).addErrback(self.errorIconDownload, item).addCallback(self.finishedIconDownload, item) for item in IconDownloadList ]
            finished = defer.DeferredList(downloads).addErrback(self.error).addCallback(self.finishedAllDownloadFiles)
        else:
            self.finishedAllDownloadFiles(None)
        if self.callback is not None:
            self.callback(self.OK, None)
        return


def download(item):
    return downloadPage(item.url, file(item.filename, 'wb'))