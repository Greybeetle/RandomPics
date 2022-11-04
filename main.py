from flask import Flask, render_template, request, redirect, send_file, url_for, current_app
import os, random, time, sys
from PIL import Image
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from _utils import randomcolor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'pics/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234qwer@localhost/db_flask'
db = SQLAlchemy(app)
IPAddr = '0.0.0.0'
Port = 5050


# 定义标签类
class pics_tags(db.Model):
    __tablename__ = 'tb_Tag'
    id = db.Column('tag_id', db.Integer, primary_key=True, autoincrement=True)
    tag = db.Column(db.String(255))
    tag_color = db.Column(db.String(255))

    def __init__(self, tag, tag_color) :
        self.tag = tag
        self.tag_color = tag_color


# 定义图片类
class pics(db.Model):
    __tablename__ = 'tb_Pics'
    id = db.Column('pics_id', db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    tag_id = db.Column(db.Integer, db.ForeignKey('tb_Tag.tag_id'))
    height = db.Column(db.Integer)
    width = db.Column(db.Integer)
    size = db.Column(db.Integer)
    type = db.Column(db.String(255))
    upload_time = db.Column(db.DateTime, default=datetime.now)
    pics_url = db.Column(db.String(255))
    
    def __init__(self, name, tag_id, height, width, size, type, pics_url):
        self.name = name
        self.tag_id = tag_id
        self.height = height
        self.width = width
        self.size = size
        self.type = type
        self.pics_url = pics_url    


"""
1. 图片保存到当前目录的pics文件夹下（子文件夹有2个，适用手机、适用电脑）
2. 路径保存到数据库中，同时数据库中还存储图片的属性（包括：标签、大小、尺寸、上传时间、类型-适用手机或电脑、图片路径等信息）
3. 可以实现带/不带标签返回随机图片的能力，需要2个路由
4. 需要实现图片上传的功能，上传过程中需要确定图片标签（可以选择已有标签、也可新建标签）、类型信息，
    其他如大小、尺寸上传时间、图片路劲（按照年月日路径）等均自动生成，图片名称按照时间戳的形式自动重命名
5. 【可选】最好是可以实现图片压缩功能，在上传图片过程中自动生成middle、small型的图片一并保存到指定文件夹下
"""


# 不带标签的随机图片
@app.route('/pics')
def random_pics():
    result = pics.query.all()
    random_result = random.choice(result)
    pics_path = os.path.join(str(random_result.pics_url), str(random_result.name))
    return send_file(pics_path)


# 按照图片id返回图片
@app.route('/pics/<name>')
def show_pics_by_id(name):
    result = pics.query.filter_by(name=name).first()
    pics_path = os.path.join(sys.path[0], str(result.pics_url), str(result.name))
    print(pics_path)
    return send_file(pics_path)


# 带标签的随机图片
@app.route('/pics/<tag>')
def random_pics_tag(tag):
    result = pics.query.filter_by(tag=tag).all()
    random_result = random.choice(result)
    pics_path = os.path.join(str(random_result.pics_url), str(random_result.name))
    return send_file(pics_path)


# 上传图片
@app.route('/upload')
def upload_pics():
    return render_template('upload.html')


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if request.method == 'POST':
        ##### 上传文件到指定目录
        # 获取表单数据
        file = request.files['picture']
        tag = request.form['selectTag']
        type = request.form['selectType']
        # 获取文件后缀，确定文件类型
        file_type = (file.filename).split('.')[-1]
        # 获取当前日期，用于拼接文件保存路径，按照年月日层级保存
        current_date = time.strftime('%Y/%m/%d', time.localtime(time.time()))
        # 获取当前日期时间，用于新文件命名
        current_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        # 保存原始文件名，用于备忘
        # origin_filename = file.filename
        # 拼接文件保存路径，最终形式为pics/年/月/日，最终新建该目录并写入数据库中
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], current_date)
        print(sys.path[0])
        if not os.path.exists(os.path.join(sys.path[0], filepath)):
            os.makedirs(os.path.join(sys.path[0], filepath))
        # 重命名文件后加上后缀
        new_filename = str(current_time) + '.' + file_type
        file_deeppath = os.path.join(sys.path[0], filepath, new_filename)
        # 保存文件到目标文件夹下
        file.save(file_deeppath)

        ##### 增加上传记录到数据库中
        # 获取图片大小size
        stat_info = os.stat(file_deeppath)
        file_size = stat_info.st_size
        # 获取图片尺寸
        img = Image.open(file_deeppath)
        w = img.width       #图片的宽
        h = img.height      #图片的高
        
        # 保存数据记录到数据库中
        # 创建标签，如有查询标签id，如无插入新标签后返回标签id
        select_tag = pics_tags.query.filter_by(tag=tag).first()
        tag_id = 0
        if not select_tag:
            tag_record = pics_tags(tag=tag, tag_color=randomcolor())
            db.session.add(tag_record)
            db.session.commit()
            # 插入完成后重新查询返回id，该步骤是否可以进行优化 --------------------->优化
            select_tag = pics_tags.query.filter_by(tag=tag).first()
        tag_id = select_tag.id
        # 插入图片信息到数据库中
        pics_record = pics(name=new_filename, tag_id=tag_id, height=h, width=w, size=file_size, type=type, pics_url=filepath)
        db.session.add(pics_record)
        db.session.commit()
        # return 'file uploaded successfully'
        return redirect(url_for('show_pics_by_id', name=new_filename))

    else:
        return render_template('upload.html')


@app.route('/nums')
def random_nums():
    ran_red = sorted(random.sample(range(1, 34), 6))
    ran_red_str = ' '.join([str(n) for n in ran_red])
    ran_blue_str = str(random.randint(1, 16))
    ran_str = ran_red_str +' ' + ran_blue_str
    return ran_str


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host=IPAddr, port=Port)

