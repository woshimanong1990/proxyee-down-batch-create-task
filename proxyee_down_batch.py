#coding:utf-8
import asyncio
import sys
import time
import os
import cgi
import re
import json

from urllib import parse
from urllib.parse import urlparse, unquote_plus

import aiohttp

async def fectch_config(session):
    # 获取配置信息，只用到了部分信息
    url = "http://127.0.0.1:26339/config"
    header={
        "Content-Type": "application/json;charset=UTF-8"
    }
    async with session.get(url, headers=header) as response:
        if response.status // 100 != 2:
            print("fectch_config, status", response.status)
            return {}
        config = await response.json()
        config_keys = ["filePath","connections","timeout","retryCount","autoRename","speedLimit"]
        new_config = {}
        # 啰嗦，应该有简单的方法
        for key in config_keys:
            new_config[key] = config.get(key,None)
        return new_config


async def get_head_info(session, url):
    # 获取 request 和 response 信息
    # {"request":{"method":"GET","url":"https://nodejs.org/dist/v8.12.0/node-v8.12.0-x64.msi",
    # "heads":{"Host":"nodejs.org","Connection":"keep-alive","User-Agent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36",
    # "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8","Referer":"nodejs.org"},"body":null},
    # "response":{"fileName":"node-v8.12.0-x64.msi","totalSize":16445440,"supportRange":true}}
    request_url = "http://127.0.0.1:26339/util/resolve"
    data={
        "method":"GET",
        "url":url,
        "heads":{},
        "body":""
    }
    header={
        "Accept":"application/json, text/plain, */*",
        "Content-Type":"application/json;charset=UTF-8",
        "Origin":"http://127.0.0.1:26339",
        "Referer":"http://127.0.0.1:26339/",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36"
    }
    #print("get header data", data)
    async with session.put(request_url, headers=header, json=data) as response:
        if response.status // 100 != 2:
            print("post_data error, status:{} reason{} ".format(response.status, await response.text()))
            return {}
        return await response.json()

async def post_data(session, data):
    # 发送一个创建任务的请求到proxyee-down
    url = "http://127.0.0.1:26339/tasks"
    header={
        "Accept":"application/json, text/plain, */*",
        "Content-Type":"application/json;charset=UTF-8",
        "Origin":"http://127.0.0.1:26339",
        "Referer":"http://127.0.0.1:26339/",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36"
    }
    #print("post data", json.dumps(data))
    async with session.post(url, headers=header, json=data) as response:
        if response.status // 100 != 2:
            print("post_data error,url:{} status:{} reason:{}".format(data.get("request",{}).get("url",""),response.status, await response.text()))
            #print(response.request_info)
            return None
        return await response.text()        

async def create_task(session, url):
    # 创建任务，需要先发送两个请求，然后post，创建任务
    config = await fectch_config(session)
    request_response_data = await get_head_info(session, url)
    if not config:
        print("config is empty")
        return
    if not request_response_data:
        print("request_response_data is empty")
        return
    data={
        "config":config,
    }
    data.update(request_response_data)
    return await post_data(session, data)

async def main(urls):
    tasks = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            task = create_task(session,url)
            tasks.append(task)
        await asyncio.gather(*tasks)
        
    

if __name__ == "__main__":
    url = "https://nodejs.org/dist/v8.12.0/node-v8.12.0-x64.msi"
    loop = asyncio.get_event_loop()
    urls = [url] # 添加自己的下载链接
    # 可以加载json的文件
    # with open("download_urls.json", "r") as f:
    #     urls = json.load(f)
    
    # loop.run_until_complete(asyncio.gather(*[main(url, 30) for url in urls[0:5]]))
    
    loop.run_until_complete(main(urls))