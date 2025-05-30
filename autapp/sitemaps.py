# autapp/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['index']  # add the name of views you want

    def location(self, item):
        return reverse(item)
