# -*- coding: utf-8 -*- 
import unittest
from app.models import Role, Product, Category, User, Order, Comment, Cart, Grade, Major
from app import db
from random import randint


class GenerateFakeTestCase(unittest.TestCase):
    #先将旧数据库删除，然后按照流程将一整个流程产生
    def test_generate_model(self):
        db.drop_all()
        db.create_all()
        Grade.insert_grades()
        Major.insert_majors()
        Role.insert_roles()
        Category.generate_fake()
        u = User(id=201330350225, 
                 username='曾钛柱', 
                 grade='大四', 
                 sex='男', 
                 major='网络工程', 
                 location='华山15栋', 
                 phone=18813757476, 
                 password='123',
                 pictureUrl='default.jpg')
        u.role = Role.query.filter_by(name='Administrator').first()
        db.session.add(u)
        db.session.commit()
        User.generate_fake(10)
        Product.generate_fake(50)
        imgs = ['数据结构.jpg', '数据库.jpg', '图形学.jpg', '计算机网络.jpg', '操作系统原理.jpg', 'Android.jpg']
        titles = ['数据结构', '数据库系统概念(原书第6版)', '计算机图形学(第四版)', '计算机网络(第6版)', 
                  '操作系统原理(第4版)', '第一行代码:Android(第2版)']
        authors = ['严蔚敏 , 吴伟民 ', '西尔伯沙茨 (Silberschatz.A.)', 
                   '赫恩 (Donald Hearn),巴克 (M.Pauline Baker),卡里瑟斯 (Warren R.Carithers)', 
                   '谢希仁 ', '庞丽萍', '郭霖']
        presses = ['清华大学计算机出版社', '机械工业出版社', '电子工业出版社', '电子工业出版社', 
                   '华中科技大学出版社', '人民邮电出版社']
        describes = ['为“数据结构”课程编写的教材，也可作为学习数据结构及其算法的c程序设计的参考教材', 
                    '全面介绍数据库系统的各种知识，透彻阐释数据库管理的基本概念', 
                    '本书共分24章，全面系统地讲解了计算机图形学的基本概念和相关技术。',
                    '全书分为10章，比较全面系统地介绍了计算机网络的发展和原理体系结构', 
                    '系统地阐述了现代操作系统的基本原理、主要功能及实现技术',
                    '本书被Android开发者誉为Android学习经典。全书系统全面、循序渐进地介绍了Android软件开发的知识、经验和技巧']
        prices = [29.40, 53.40, 31.20, 28.3, 18.89, 0.1]
        for i in range(len(imgs)):
            p = Product(pictureUrl=imgs[i],
                        title=titles[i],
                        author=authors[i],
                        press=presses[i],
                        count=randint(0, 4),
                        price=prices[i],
                        describe=describes[i],
                        seller=User.query.get(201330350225),
                        category=Category.query.get(1))
            db.session.add(p)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
        Order.generate_fake(100)
        Cart.generate_fake(200)
        Comment.generate_fake(200)
        self.assertTrue(Comment.query.all() is not None)
        
#     #将数据库的数据全部清空
#     def test_init_database(self):
#         db.drop_all()
#         db.create_all()
#     def test_generate_role(self):
#         Role.insert_roles()
#         self.assertTrue(Role.query.all() is not None)
#         
#     def test_generate_category(self):
#         Category.generate_fake()
#         self.assertTrue(Category.query.all() is not None)
#         
#     def test_generate_product(self):
#         Product.generate_fake()
#         self.assertTrue(Product.query.all() is not None)
#     
#     def test_insert_user(self):
#         u = User(id=201330350225, username='曾钛柱', grade='大四', sex='男', major='网络工程', location='华山15栋', phone=18813757476, password='123')
#         u.role = Role.query.filter_by(name='Administrator').first()
#         db.session.add(u)
#         db.session.commit()
#         self.assertTrue(User.query.get(201330350225).role is not None)
#     
#     def test_generate_user(self):
#         User.generate_fake()
#         self.assertTrue(User.query.count() > 1)
#         
#     def test_generate_order(self):
#         Order.generate_fake()
#         self.assertTrue(Order.query.all() is not None)
