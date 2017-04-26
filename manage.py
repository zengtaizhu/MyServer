#!/usr/bin/env python
#encoding:  utf-8 
#用于启动程序
import os
#覆盖测试
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')#启动覆盖检测
    COV.start()
    
from app import create_app, db
from app.models import User, Role, Permission, Category, Search
from app.models import Product, Order, Comment, Cart, Grade, Major
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Search=Search,
                Category=Category, Product=Product, Order=Order,
                Comment=Comment, Cart=Cart, Grade=Grade, Major=Major)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

#自定义命令
@manager.command
def test(coverage=False):
    """Run the unit tests."""#帮助文档
    if coverage and not os.environ.get('FLASK_COVERAGE'):#设定完'FLASK_COVERAGE'后重启脚本
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print(u'覆盖详情：')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        #将报告以HTML保存，covdir为保存目录
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()

#在请求分析器的监视下运行程序
@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()

#部署命令：每次安装或升级程序只需运行此命令即可
@manager.command
def deploy():
    """Run deplyment tasks."""
    from flask_migrate import upgrade
    from app.models import Role, User
    
    #将数据库迁移到最新修订版本
    upgrade()
    #创建用户数据
    Role.insert_roles()
    
    
if __name__ == '__main__':
    manager.run()
