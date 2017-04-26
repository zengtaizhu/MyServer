# -*- coding: utf-8 -*- 
#模拟浏览器，测试Web程序
import unittest
from flask import url_for
from app.models import Role, Product, Category, User, Order
from app import db, create_app
import re

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    #测试首页
    def test_home_page(self):
        response = self.client.get(url_for('main.index'))
        self.assertTrue(u'匿名用户' in response.get_data(as_text=True))#as_text：得到一个unicode字符串
        
    def test_register_and_login(self):
        #注册新用户
        response = self.client.post(url_for('auth.register'), data={
            'id':'777777777777',
            'username':'测试',
            'password':'123',
            'password2':'123',
            'grade':'大一',
            'major':'网络工程',
            'location':'华山14栋',
            'phone':'18813757490'
        })
        self.assertTrue(response.status_code == 302)#302表示重定向，指注册成功
        
        #使用新注册的账号登录
        response = self.client.post(url_for('auth.login'), data={
            'account':'777777777777',
            'password':'123'
            }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue(re.search('您好,\s+测试!', data))
        
        #退出登录
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertTrue('您好, 匿名用户!' in data)
        
        