#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2019/7/5 4:00 PM
# @Author  : w8ay
# @File    : spiderset.py
import threading
import urllib
from urllib import parse as urlparse
from urllib.request import unquote

from thirdpart.simhash import Simhash

Chars = [',', '-', '_']


def url_etl(url):
    '''
    url泛化处理
    :param url: 原始url
    :return: 处理过后的url
    '''
    params_new = {}
    u = urlparse.urlparse(url)
    query = unquote(u.query)
    query_new = ''
    if query:
        params = urlparse.parse_qsl(query, True)
        for k, v in params:
            if v:
                params_new[k] = etl(v)
        query_new = urllib.parse.urlencode(params_new)

    path_new = etl(u.path, True)

    url_new = urlparse.urlunparse(
        (u.scheme, u.netloc, path_new, u.params, query_new, u.fragment))
    return url_new


def etl(str, onlyNUM=False):
    '''
    传入一个字符串，将里面的字母转化为A，数字转化为N，特殊符号转换为T，其他符号或者字符转化成C
    :param str:
    :param onlyNUM:只换数字
    :return:
    '''
    if not str:
        return ""
    
    str_lower = str.lower()
    chars = []
    
    if not onlyNUM:
        for c in str_lower:
            if 'a' <= c <= 'z':
                chars.append('A')
            elif '0' <= c <= '9':
                chars.append('N')
            elif c in Chars:
                chars.append('T')
            else:
                chars.append('C')
    else:
        for c in str_lower:
            if '0' <= c <= '9':
                chars.append('N')
            else:
                chars.append(c)
    
    return ''.join(chars)


def url_compare(url, link):
    dis = Simhash(url).distance(Simhash(link))
    if -2 < dis < 5:
        return True
    else:
        return False


def reduce_urls(ori_urls):
    '''
    对url列表去重
    :param ori_urls: 原始url列表
    :return: 去重后的url列表
    '''
    etl_urls = []
    result_urls = []
    for ori_url in ori_urls:
        etl = url_etl(ori_url)
        print(etl)
        score = 0
        if etl_urls:
            for etl_url in etl_urls:
                if not url_compare(etl, etl_url):
                    score += 1

            if score == len(etl_urls):
                result_urls.append(ori_url)
                etl_urls.append(etl)
        else:
            etl_urls.append(etl)
            result_urls.append(ori_url)

    return result_urls


class SpiderSet(object):
    """
    基于Google Simhash算法，优化版本使用缓存提高性能
    """

    def __init__(self):
        self.spider_list = {
            "PerFile": {},
            "PerFolder": {},
            "PerServer": {},
            "PostScan": {}
        }
        self.simhash_cache = {}
        self.lock = threading.Lock()

    def _get_simhash(self, etl_url):
        """
        获取URL的Simhash值，使用缓存避免重复计算
        :param etl_url: ETL处理后的URL
        :return: Simhash对象
        """
        if etl_url not in self.simhash_cache:
            self.simhash_cache[etl_url] = Simhash(etl_url)
        return self.simhash_cache[etl_url]

    def add(self, url, plugin):
        """
        添加成功返回True，添加失败有重复返回False
        :param url:
        :param plugin:
        :return:bool
        """
        ret = True
        if not (isinstance(url, str) and isinstance(plugin, str)):
            url = str(url)
            plugin = str(plugin)

        self.lock.acquire()
        try:
            if plugin not in self.spider_list:
                self.spider_list[plugin] = {}
            netloc = urlparse.urlparse(url).netloc
            if netloc not in self.spider_list[plugin]:
                self.spider_list[plugin][netloc] = []
            
            etl = url_etl(url)  # url泛化表达式
            
            # 提前计算当前URL的Simhash，只计算一次
            etl_simhash = self._get_simhash(etl)
            
            # 快速检查是否已存在完全相同的ETL
            if etl in self.spider_list[plugin][netloc]:
                ret = False
            else:
                # 使用预计算的Simhash进行比较
                is_duplicate = False
                for existing_etl in self.spider_list[plugin][netloc]:
                    existing_simhash = self._get_simhash(existing_etl)
                    dis = etl_simhash.distance(existing_simhash)
                    if -2 < dis < 5:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    self.spider_list[plugin][netloc].append(etl)
                else:
                    ret = False
        finally:
            self.lock.release()
        
        return ret
