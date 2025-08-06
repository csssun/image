from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import base64
import time
import json
import hashlib
import urllib.parse
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # 允许跨域请求

def generate_token(e: str, timestamp: str) -> str:
    """生成百度API所需的token"""
    s = hashlib.md5(e.encode('utf-8')).hexdigest()
    combined = s + "pic_edit" + timestamp
    final_hash = hashlib.md5(combined.encode('utf-8')).hexdigest()
    return final_hash[:5]

def upload_to_baidu(base64_string):
    """上传图片到百度图床"""
    url = "https://image.baidu.com/aigc/pic_upload"
    
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Origin': 'https://image.baidu.com',
        'Pragma': 'no-cache',
        'Referer': 'https://image.baidu.com/search/index?tn=baiduimage&ipn=r&ct=201326592&cl=2&lm=-1&st=-1&fm=detail&hs=0&xthttps=111110&sf=1&fmq=1713767239197_R&pv=&ic=0&nc=1&z=&se=&showtab=0&fb=0&width=&height=&face=0&istype=2&ie=utf-8&word=bdaitpzs%E7%99%BE%E5%BA%A6AI%E5%9B%BE%E7%89%87%E5%8A%A9%E6%89%8Bbdaitpzs&oq=%E5%9B%BE%E7%89%87&rsp=-1&toolType=1&fr=home&sa=searchpromo_shijian_photohp_dewatermark&showMask=1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }
    
    timestamp = str(int(time.time() * 1000))
    
    # 构建图片数据
    e = f'data:image/jpeg;base64,{base64_string}'
    token = generate_token(e, timestamp)
    
    payload = {
        "token": token,
        "scene": "pic_edit", 
        "picInfo": e,
        "timestamp": timestamp,
    }
    
    payload = urllib.parse.urlencode(payload)
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'data' in result and 'url' in result['data']:
            return result['data']['url']
        else:
            raise Exception(f"百度API返回异常: {result}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求错误: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"响应解析错误: {str(e)}")

@app.route('/upload', methods=['POST'])
def upload_image():
    """处理图片上传请求"""
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({'success': False, 'error': '缺少图片数据'}), 400
        
        base64_string = data['image']
        filename = data.get('filename', 'image.jpg')
        
        # 验证base64数据
        if not base64_string:
            return jsonify({'success': False, 'error': '图片数据为空'}), 400
        
        # 尝试解码base64来验证数据有效性
        try:
            base64.b64decode(base64_string)
        except Exception as e:
            return jsonify({'success': False, 'error': '无效的图片数据'}), 400
        
        # 上传到百度图床
        image_url = upload_to_baidu(base64_string)
        
        return jsonify({
            'success': True,
            'url': image_url,
            'filename': filename
        })
        
    except Exception as e:
        print(f"上传错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'ok', 'message': '服务运行正常'})

@app.route('/', methods=['GET'])
def index():
    """根路径返回API信息"""
    return jsonify({
        'name': '百度图床上传API',
        'version': '1.0.0',
        'endpoints': {
            '/upload': 'POST - 上传图片',
            '/health': 'GET - 健康检查'
        }
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 百度图床上传服务启动中...")
    print("=" * 50)
    print("📝 API接口:")
    print("   POST /upload - 上传图片")
    print("   GET  /health - 健康检查")
    print("=" * 50)
    print("🌐 前端访问地址: 打开 HTML 文件")
    print("🔧 后端服务地址: http://localhost:5000")
    print("=" * 50)
    
    # 开发模式运行
    app.run(debug=True, host='0.0.0.0', port=5000)
