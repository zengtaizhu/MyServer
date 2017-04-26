# -*- coding: utf-8 -*- 
#密码散列化测试
import unittest
from app.models import User, AnonymousUser, Role, Permission

class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)
    
    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password
            
    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))
        
    def test_password_salts_are_random(self):
        u1 = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u1.password_hash != u2.password_hash)
        
    #角色和权限的单元测试
    def test_roles_and_permission(self):
        Role.insert_roles()
        u = User(password='cat')
        self.assertTrue(u.can(Permission.BUY))
        self.assertFalse(u.can(Permission.ADMINISTER))
        
    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.BUY))