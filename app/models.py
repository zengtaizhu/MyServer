#encoding:  utf-8
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from flask_login import UserMixin, AnonymousUserMixin
from datetime import datetime
from flask import current_app, url_for, request
from builtins import staticmethod
from app.exceptions import ValidationError
import hashlib
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from pip._vendor.distlib.util import _external_data_base_url
import forgery_py
import json
from sqlalchemy.orm.relationships import foreign
from sqlalchemy.orm import backref
from email.policy import default
from _operator import index
from pydoc import describe
from random import random
from test.test_buffer import randitems
from sqlalchemy.exc import IntegrityError

GRADE = ['大一' ,'大二','大三', '大四', '研究生', '所有人']#年级常量
SEX = ['男', '女']#性别常量
MAJOR = ['电子信息科学与技术', '农学', '木材科学与工程', '生物工程', '电子信息工程', '电子科学与技术', '网络工程']#专业常量，以后用数据库代替
OrderState = {'DELIVERING':'待发货', 'RECEIVEING':'待收货','COMMENTING':'待评价', 'DONE':'交易成功', 'RETURNING':'退货'}#订单状态常量
SECRET_KEY = 'you are my all'#加密钥匙
Flasky_Per_Page = 6#每一页的记录数量
PIC_PATH = 'E:\\code\\Python\\BookStore\\BookStore\\app\\static\\picture'#图片主目录
IP = 'http://192.168.191.1:5000/static/picture/'#图片的网址路径

#年级常量表
class Grade(db.Model):
    __tablename_ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    
    @staticmethod
    def insert_grades():
        grade = ['大一' ,'大二','大三', '大四', '研究生', '所有人']
        for g in grade:
            g = Grade(name=g)
            db.session.add(g)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        
    def __repr__(self):
        return '<Grade %r>' % self.name


#专业常量表
class Major(db.Model):
    __tablename__ = 'majors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    
    @staticmethod
    def insert_majors():
        major = ['电子信息科学与技术', '农学', '木材科学与工程', '生物工程', '电子信息工程', '电子科学与技术', '网络工程']
        for m in major:
            m = Major(name=m)
            db.session.add(m)
        db.session.commit()
        
    def __repr__(self):
        return '<Major %r>' % self.name
    

class Permission:#权限常量
    BUY = 0x01
    ORDER_MANAGER = 0x02
    BOOK_MANAGER = 0x04
    ADMINISTER = 0x80

#角色表
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)#用于设置用户注册后的默认角色
    permissions = db.Column(db.Integer)#用户权限
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    #初始化Role数据库
    @staticmethod
    def insert_roles():
        roles = {
            'BlacklistUser':(Permission.BUY, False),
            'User':(Permission.BUY|
                    Permission.BOOK_MANAGER|
                    Permission.ORDER_MANAGER, True),#True：表示用户注册后的默认角色是User
            'Administrator':(0xff, False)
            }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
               role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()
        
    def __repr__(self):
        return '<Role %r>' % self.name


#订单表    
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    orderId = db.Column(db.Text(), nullable=False)#使用第三方网站的订单号，仅仅保存在服务器
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'))  
    #products包含多个商品,格式为：ID|count,ID2|count2...
    products = db.Column(db.Text(), nullable=False)
    submit_time = db.Column(db.DateTime(), default=datetime.now)
    deliver_time = db.Column(db.DateTime(), default=datetime.now)
    state = db.Column(db.String(64), nullable=False, default=OrderState.get('DELIVERING'))
    phone = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(64), nullable=False)
    totalprice = db.Column(db.Float, nullable=False)
    sendWay = db.Column(db.Text(), nullable=False, default='快递 到付')
    courier = db.Column(db.String(12))#快递单号
    comment = db.Column(db.Text())
    
    @staticmethod
    def generate_fake(count=100):
        from random import randint, seed
        from sqlalchemy.exc import IntegrityError
        import forgery_py
        import random
        
        seed()
        user_count = User.query.count()
        product_count = Product.query.count()
        for i in range(count):                                 #--------下面除2时注意要整数，待修改------
            o = User.query.offset(randint(0, int(user_count / 2))).first()#每次获得一个随机用户(卖家)
            b = User.query.offset(randint(int(user_count / 2), user_count-1)).first()#每次获得一个随机用户(买家)
            productids = ''#格式为：ID|count,ID2|count2...
            totalprices = 0#订单总价格
            for x in range(randint(1, 3)):
                p = Product.query.offset(randint(0, product_count-1)).first()#每次随机获得一个随机商品
                count = randint(1, 3)
                productids += str(p.id) + '|' + str(count) + ','
                totalprices += count * p.price
            order = Order(products=productids,
                      submit_time=forgery_py.date.date(True),
                      orderId=forgery_py.lorem_ipsum.word(),
                      deliver_time=forgery_py.date.date(False),
                      state=random.choice(list(OrderState.values())),
                      phone=b.phone,
                      address=b.location,
                      totalprice=totalprices,
                      comment=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                      seller=o,
                      buyer=b,
                      sendWay='快递 到付',
                      courier=randint(1, 10000000))
            db.session.add(order)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
              
    def __repr__(self):
        return '<Order %r>' % self.id
    
    #将订单转化为JSON数据(买家)
    def to_json(self):
        #先将products解析为Product列表，products格式为：ID|count,ID2|count2,
        import re
        list = re.findall(r'(\d+)\|(\d+),', self.products)
        productList = []
        for item in list:
            product = Product.query.get(int(item[0]))#找到该商品
            if product is None:
                continue
            product.count = int(item[1])#设置该商品的数量
            productList.append(product)
        json_order = {
                'id': self.id,
                'orderId': self.orderId,
                'products': [product.to_json() for product in productList],
                'submit_time': self.submit_time.strftime('%Y-%m-%d %H:%M:%S'),
                'deliver_time': self.deliver_time.strftime('%Y-%m-%d %H:%M:%S'),
                'state': self.state,
                'phone': self.phone,
                'address': self.address,
                'totalprice': self.totalprice,
                'comment': self.comment,
                'sendWay': self.sendWay,
                'courier': self.courier,
                'user_id': self.seller_id,
                'user_img': self.seller.pictureUrl
            }
        return json_order
    
    #将订单转化为JSON数据(卖家)
    def to_json_own(self):
        #先将products解析为Product列表，products格式为：ID|count,ID2|count2,
        import re
        list = re.findall(r'(\d+)\|(\d+),', self.products)
        productList = []
        for item in list:
            product = Product.query.get(int(item[0]))#找到该商品
            if product is None:
                continue
            product.count = int(item[1])#设置该商品的数量
            productList.append(product)
        json_order = {
                'id': self.id,
                'orderId': self.orderId,
                'products': [product.to_json() for product in productList],
                'submit_time': self.submit_time.strftime('%Y-%m-%d %H:%M:%S'),
                'deliver_time': self.deliver_time.strftime('%Y-%m-%d %H:%M:%S'),
                'state': self.state,
                'phone': self.phone,
                'address': self.address,
                'totalprice': self.totalprice,
                'comment': self.comment,
                'sendWay':self.sendWay,
                'courier': self.courier,
                'user_id': self.buyer_id,
                'user_img':self.buyer.pictureUrl
            }
        return json_order
        
#购物车表        
class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'))  
    #products包含多个商品,格式为：ID|count,ID2|count2...
    products = db.Column(db.Text(), nullable=False)
    totalprice = db.Column(db.Float, nullable=False)
    
    @staticmethod
    def generate_fake(count=100):
        from random import randint, seed
        from sqlalchemy.exc import IntegrityError
        import forgery_py
        import random
        
        seed()
        user_count = User.query.count()
        product_count = Product.query.count()
        for i in range(count):                                 
            o = User.query.offset(randint(0, int(user_count / 2))).first()#每次获得一个随机用户(卖家)
            b = User.query.offset(randint(int(user_count / 2), user_count-1)).first()#每次获得一个随机用户(买家)
            productids = ''#格式为：ID|count,ID2|count2,...
            totalprices = 0#订单总价格
            for x in range(randint(1, 3)):
                p = Product.query.offset(randint(0, product_count-1)).first()#每次随机获得一个随机商品
                count = randint(1, 3)
                productids += str(p.id) + '|' + str(count) + ','
                totalprices += count * p.price
            cart = Cart(products=productids,
                      totalprice=totalprices,
                      seller=o,
                      buyer=b)
            db.session.add(cart)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
              
    def __repr__(self):
        return '<Cart %r>' % self.id
    
    #将订单转化为JSON数据
    def to_json(self):
        #先将products解析为Product列表，products格式为：ID|count,ID2|count2,
        import re
        list = re.findall(r'(\d+)\|(\d+),', self.products)
        json_order = {
                'id': self.id,
                'products': [self.product_to_json(int(item[0]), int(item[1])) for item in list],
                'totalprice': self.totalprice,
                'seller': self.seller_id
            }
        return json_order
    
    #获得Cart的商品列表
    @staticmethod
    def product_to_json(id, count):
        product = Product.query.get(id)#找到该商品
        if product is None:
            return {}
        json_product = {
                'id': product.id,
                'category_id': product.category_id,
                'seller_id': product.seller_id,
                'pictureUrl':product.pictureUrl,
                'title': product.title,
                'author':product.author,
                'press':product.press,
                'price': product.price,
                'count': count,
                'describe': product.describe
            }
        return json_product
    
    #从JSON格式数据创建订单
    @staticmethod
    def from_json(json_order):
        products = json_order.get('products')
        totalprice = json_order.get('totalprice')
        seller_id = json_order.get('seller_id')
        buyer_id = json_order.get('buyer_id')
        if seller_id is None or seller_id == '':
            raise ValidationError('订单没有卖家')
        if buyer_id is None or buyer_id == '':
            raise ValidationError('订单没有买家')
        seller = User.query.get(seller_id)
        buyer = User.query.get(buyer_id)
        return Cart(products=products,
                     totalprice=totalprice,
                     seller=seller,
                     buyer=buyer)


#UserMixin支持用户登录
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    pictureUrl = db.Column(db.Text(), default='0.jpg')
    username = db.Column(db.String(20), index=True, default='未知用户')
    grade = db.Column(db.String(10), default='大一')
    sex = db.Column(db.String(10), default='男')
    major = db.Column(db.String(20), default='无')
    location = db.Column(db.String(64), default='华南农业大学')
    phone = db.Column(db.Integer, unique=True)
    more = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.now)
    last_seen = db.Column(db.DateTime(), default=datetime.now)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    products = db.relationship('Product', backref='seller', lazy='dynamic')
    writer = db.relationship('Comment', backref='buyer', lazy='dynamic')
    orders = db.relationship('Order', foreign_keys=[Order.buyer_id],
                             backref=db.backref('buyer', lazy='joined'), 
                             lazy='dynamic', cascade='all, delete-orphan')#购买商品的订单
    owners = db.relationship('Order', foreign_keys=[Order.seller_id], 
                             backref=db.backref('seller', lazy='joined'), 
                             lazy='dynamic', cascade='all, delete-orphan')#销售商品的订单
    cartOrder = db.relationship('Cart', foreign_keys=[Cart.buyer_id],
                             backref=db.backref('buyer', lazy='joined'), 
                             lazy='dynamic', cascade='all, delete-orphan')#购买商品的购物车
    cartOwner = db.relationship('Cart', foreign_keys=[Cart.seller_id], 
                             backref=db.backref('seller', lazy='joined'), 
                             lazy='dynamic', cascade='all, delete-orphan')#销售商品的购物车
#     confirmed = db.Column(db.Boolean, default=False)#用于确认是否注册成功

    @staticmethod #虚拟生成用户
    def generate_fake(count=20):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import random
        import forgery_py
        
        seed() 
        grades = [g.name for g in Grade.query.all()]
        majors = [m.name for m in Major.query.all()]
        for i in range(count):
            u = User(username=forgery_py.internet.user_name(True),
                     grade=random.choice(grades),
                     sex=random.choice(SEX),
                     major=random.choice(majors),
                     location=forgery_py.address.city(),
                     phone=forgery_py.address.phone(),
                     more=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                     member_since=forgery_py.date.date(True),
                     password='123',
                     pictureUrl=str(randint(0, 9)) + '.jpg')
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                                  
    #完成初始化，将用户角色设置为默认角色
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role_id is None:
            #如果User的角色是None，则角色设置为User
            self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    #设置密码
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    #验证密码
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username
    
    #角色权限验证
    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions
            
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)
    
    #刷新用户最后的访问时间
    def ping(self):
        self.last_seen = datetime.now()
        db.session.add(self)
    
    #生成安全令牌
    def generate_auth_token(self, expiration):
        s = Serializer(SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id})
        
    #验证安全令牌
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(SECRET_KEY)
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])
    
    #将用户转化为JSON格式的序列化字典(带令牌)
    def to_json_with_token(self):
        json_user = {
                'id': self.id,
                'pictureUrl': IP + 'users/' +self.pictureUrl,
                'username': self.username,
                'passwordOrToken': self.generate_auth_token(expiration=3600).decode(),
                'grade': self.grade,
                'sex': self.sex,
                'major': self.major,
                'location':self.location,
                'phone': self.phone,
                'more': self.more
            }
        return json_user
    
    #将用户转化为JSON格式的序列化字典(不带令牌)
    def to_json(self):
        json_user = {
                'id': self.id,
                'pictureUrl': IP + 'users/' + self.pictureUrl,
                'username': self.username,
                'passwordOrToken': '',
                'grade': self.grade,
                'sex': self.sex,
                'major': self.major,
                'location':self.location,
                'phone': self.phone,
                'more': self.more
            }
        return json_user
    
#匿名用户：不用先检查用户是否登录即可检查权限
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    
    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser    

#加载用户的回调函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#商品类别表      
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False, index=True)
    suitableGrade = db.Column(db.String(64), nullable=False, index=True)
    pictureUrl = db.Column(db.Text(), default="default.jpg")
    describe = db.Column(db.Text(), nullable=False)
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    @staticmethod#虚拟生成商品类别
    def generate_fake():
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import forgery_py
        
        seed()
        grades = [g.name for g in Grade.query.all()]
        majors = [m.name for m in Major.query.all()]
        categories = ['计算机', '语文', '法律', '英语', '经管', '艺术', '医药卫生', '公共管理', '数理化',
                      '工科', '农林牧渔', '文史哲', '体育', '毕业论文指导', '心理健康与生活指南']
        describes = ['计算机知识库', '文学类书籍', '法律指导', '英语学习之路', '经济的海洋', '人生的艺术', '人体的奥妙',
                     '公共事务的管理学习', '理科生的天堂', '工科的磨刀石', '农林牧渔 包罗万象', '文艺的气息', '运动知识', '毕业论文的直达之路',
                     '心理辅导与自我了解']
        for i in range(len(categories)):
            category = Category(name=categories[i],
                                suitableGrade=grades[randint(0, len(grades) - 1)],
                                pictureUrl = str(i) + '.jpg',
                                describe=describes[i]
                                )
            db.session.add(category)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                
            
    def __repr__(self):
        return '<Category %r>' % self.name
    
    #将商品类转化为JSON数据
    def to_json(self):
        json_category = {
                'id': self.id,
                'name': self.name,
                'suitableGrade': self.suitableGrade,
                'pictureUrl': IP + 'categories/' + self.pictureUrl,
                'describe': self.describe
            }
        return json_category
    

#商品表
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    pictureUrl = db.Column(db.Text(), default='default.jpg')
    title = db.Column(db.String(50), nullable=False, index=True)
    author = db.Column(db.String(50), index=True)
    press = db.Column(db.String(50))#出版社
    count = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0)
    describe = db.Column(db.Text())
    comments = db.relationship('Comment', backref='product', lazy='dynamic')
    
    @staticmethod#虚拟生成商品
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint, choice
        import forgery_py
        
        seed()
        user_count = User.query.count()
        category_count = Category.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()#随机获得一个用户
            c = Category.query.offset(randint(1, category_count - 1)).first()#随机获得一个商品类
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
            p = Product(pictureUrl=str(randint(0, 14)) + '.jpg',
                        title=choice(titles),
                        author=choice(authors),
                        press=choice(presses),
                        count=randint(0, 10),
                        price=round(randint(0, 19999) * 0.01, 2),
                        describe=choice(describes),
                        seller=u,
                        category=c)
            db.session.add(p)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
            
    def __repr__(self):
        return '<Product %r>' % self.id

    #将商品转化为JSON数据
    def to_json(self):
        json_product = {
                'id': self.id,
                'category_id': self.category_id,
                'seller_id': self.seller_id,
                'pictureUrl': IP + 'products/' + self.pictureUrl,
                'title': self.title,
                'author':self.author,
                'press':self.press,
                'price': self.price,
                'count': self.count,
                'describe': self.describe,
                'suitableGrade': self.category.suitableGrade#适合的年级
            }
        return json_product
    
    #将商品以广告的形式转化为JSON数据
    def to_recommend_json(self):
        json_product = {
                'proId':self.id,
                'imgUrl':IP + 'products/' + self.pictureUrl,
                'proName':self.title
            }
        return json_product    


#评论表
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    buyer_img = db.Column(db.Text())
    comment_time = db.Column(db.DateTime(), default=datetime.now)
    comment = db.Column(db.Text(), nullable=False);
    
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import randint, seed, choice
        import forgery_py
        
        seed()
        product_count = Product.query.count() 
        user_count = User.query.count()
        comments = ['不错，这是一本好书', '这本书还是挺新的，价格也挺合理', '默认好评', '终于拿到手了，很不错的书']
        for i in range(count):
            p = Product.query.offset(randint(0, product_count - 1)).first()#随机获取一个商品
            u = User.query.offset(randint(0, user_count - 1)).first()#随机获得一个买家
            c = Comment(product=p,
                        buyer=u,
                        buyer_img = u.pictureUrl,
                        comment_time=datetime.now(),
#                         grade=randint(1, 5),
                        comment=choice(comments))
            db.session.add(c)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
    
    def __repr__(self):
        return '<Comment %r>' % self.id
    
    #转化为JSON数据
    def to_json(self):
        json_comment = {
            'id':self.id,
            'buyer_id':self.buyer_id,
            'buyer_img':IP + 'users/' + self.buyer_img,
            'comment_time':self.comment_time.strftime('%Y-%m-%d %H:%M'),
#             'grade':self.grade,
            'comment':self.comment
            }
        return json_comment

#搜索记录表   
class Search(db.Model):
    __tablename__ = 'searches'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(20), nullable=False)
    count = db.Column(db.Integer, index=True, default=1)
#     grade = db.Column(db.String(64), nullable=False)
#     major = db.Column(db.String(64), nullable=False)
    
    def __repr__(self):
        return '<Search %r>' % self.key
    
    
    
    
    
    
    
    
    
    
    
    
        