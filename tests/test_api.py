# -*- coding: utf-8 -*- 
#模拟移动端，测试Web程序
import unittest
import json
from flask import url_for
from app.models import Role, Product, Category, User, Order
from app import db, create_app
from base64 import b64encode

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def get_api_headers(self, username, password):
        return{
            'Authorization':
                'Basic' + b64encode(
                    (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept':'application/json',
            'Content-Type':'application/json'
            }
    
    #有错误  -----------待修改，修改为登录后才能访问
    def  test_no_auth(self):
        response = self.client.get(url_for('api.get_products'),
                                   content_type='application/json')
        self.assertTrue(response.status_code == 200)
    
    def test_products(self):
        #添加一个用户
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(id='333333333333', password='123', role=r)
        db.session.add(u)
        db.session.commit()
        
        #获取商品信息
        response = self.client.get(
            'http://127.0.0.1:5000/api/v1.0/products/',
            headers=self.get_api_headers('333333333333', '123'))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['count'] is not None)
        
        
        #提交订单、添加购物车等等   --------------待补充
        
        
        